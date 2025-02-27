import datetime
import json
import os
from functools import lru_cache
from typing import TypeAlias
from uuid import UUID

from globus_sdk import AuthClient
from globus_sdk import ClientApp
from globus_sdk import SearchClient
from globus_sdk import SpecificFlowClient
from globus_sdk import TimerClient
from globus_sdk import TimerJob
from globus_sdk.scopes import TimerScopes
from globus_sdk.services.search.errors import SearchAPIError
from globus_sdk.utils import slash_join

from aero.config import Config

from aero.globus.utils import FlowEnum
from aero.globus.utils import FLOW_IDS

JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None


class GlobusClient:
    app: ClientApp
    auth_client: AuthClient
    timer_client: TimerClient
    search_client: SearchClient
    search_index: str

    def __init__(self, search_index=None):
        self.app = ClientApp(
            "aero",
            client_id=Config.PORTAL_CLIENT_ID,
            client_secret=Config.PORTAL_CLIENT_SECRET,
        )
        self.specific_flow_clients = {}

        for flow_id in FLOW_IDS.values():
            self.specific_flow_clients[flow_id] = SpecificFlowClient(
                flow_id=flow_id, app=self.app
            )

        self.auth_client = AuthClient(app=self.app)
        self.timer_client = TimerClient(app=self.app, app_scopes=self._timer_scopes())
        self.search_client = SearchClient(app=self.app)
        self.search_client.add_app_scope(self.search_client.scopes.all)
        self.search_index = search_index

    def _create_search_idx(self):
        if self.search_index is None:
            r = self.search_client.create_index(
                "AERO data",
                "Searchable index for all AERO data",
            )
            self.search_index = r["id"]
            print(f"Created new search index: {self.search_index}")

    def _timer_scopes(self):
        timer_scope = TimerScopes.make_mutable("timer")
        for sfc in self.specific_flow_clients.values():
            timer_scope.add_dependency(sfc.scopes.user)

        return timer_scope

    def add_search_entry(self, entry: dict) -> str:
        try:
            response = self.search_client.ingest(self.search_index, entry)
            return response.text
        except SearchAPIError as e:
            return e.raw_json

    @lru_cache
    def get_user_uuid(self, usernames: str):
        return self.auth_client.get_identities(usernames=usernames)["identities"][0][
            "id"
        ]

    def run_flow(
        self,
        endpoint_uuid: str,
        function_uuid: str,
        pull_function_uuid: str,
        commit_function_uuid: str,
        tasks: JSON,
        email: str | None,
    ):
        flow_id = FLOW_IDS[FlowEnum.USER_FLOW]

        monitors = []

        if isinstance(tasks, dict):
            tasks = [tasks]

        if email is not None:
            user_uuid = self.get_user_uuid(usernames=email)
            monitors.append(user_uuid)

        run_input = {
            "endpoint": endpoint_uuid,
            "version_function": pull_function_uuid,
            "commit_function": commit_function_uuid,
            "function": function_uuid,
            "tasks": tasks,
        }
        response = self.specific_flow_clients[flow_id].run_flow(
            body=run_input,
            label="AERO Demo | User flow",
            run_managers=monitors,
        )
        assert response.http_status == 201

    def set_timer(
        self,
        interval_in_sec: int,
        id: int,
        email: str,
        flow_type: FlowEnum,
        user_function: str,
        pull_function_uuid: str,
        commit_function_uuid: str,
        function_args: str,
        user_endpoint: str,
        **kwargs,
    ) -> UUID:
        """Set a Globus Timer for daily retrieval of updated tables from sources.

        Arguments:
            func_uuid: The Globus Compute registered function UUID.
        """
        flow_id = FLOW_IDS[flow_type]

        if email is None:
            email = ""

        kwargs = function_args["kwargs"]
        if flow_type == FlowEnum.VERIFY_AND_MODIFY:
            run_input = {
                "osprey-worker-endpoint": str(user_endpoint),
                "download-function": pull_function_uuid,
                "database-commit-function": commit_function_uuid,
                "user-wrapper-function": user_function,
                "kwargs": json.dumps(kwargs),
                "author-email": email,
                "_private_password": os.environ.get("DSAAS_EMAIL_PASSWORD"),
            }
            run_label = f"AERO Demo | Ingestion flow {str(id)[:8]}"
            name = f"AERO-ingestion-{str(id)[:8]}"

        else:
            run_input = {
                "endpoint": user_endpoint,
                "version_function": pull_function_uuid,
                "commit_function": commit_function_uuid,
                "function": user_function,
                "tasks": json.dumps(kwargs),
            }
            run_label = "AERO Demo | User flow"
            name = f"AERO-user-flow-{id}"

        url = slash_join(
            self.specific_flow_clients[flow_id].base_url,
            f"/flows/{flow_id}/run",
        )

        # TODO: TimerJob is now considered legacy.
        # run_as, run_monitor, run_manage all currently unsupported
        job = TimerJob(
            callback_url=url,
            callback_body={"body": run_input, "label": run_label},
            start=datetime.datetime.now(),
            interval=datetime.timedelta(seconds=interval_in_sec),
            name=name,
            scope=self.specific_flow_clients[flow_id].scopes.user,
        )

        response = self.timer_client.create_job(job)
        assert response.http_status == 201
        job_id = UUID(response["job_id"])
        return job_id

    def delete_job(self, job_id: str):
        response = self.timer_client.delete_job(job_id=job_id)
        assert response.http_status == 200, response.http_reason
