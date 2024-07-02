import datetime
import json
import os

from globus_sdk import TimerClient
from globus_sdk import TimerJob
from globus_sdk.utils import slash_join
from globus_sdk import SpecificFlowClient
from osprey.server.lib.globus_flow import create_authorizer, FLOW_IDS, FlowEnum
from osprey.server.config import Config

"""

This module creates a job that gets triggered by Globus Timer.

-> The flow IDs stored in lib.globus_flow can be recreated in `globus.org` by using the files from osprey/workflow/

-> To run the TimerJob, there should be authentication file that should store the token with the scope ( Ensure it run before starting the project )

"""


def set_timer(
    interval_in_sec: int,
    id: int,
    email: str,
    flow_type: FlowEnum,
    user_endpoint: str,
    **kwargs,
) -> None:
    """Set a Globus Timer for daily retrieval of updated tables from sources.

    Arguments:
        func_uuid: The Globus Compute registered function UUID.
    """
    flow_id = FLOW_IDS[flow_type]

    sfc = SpecificFlowClient(flow_id=flow_id)
    authorizer, specific_flow_scope = create_authorizer(flow_id)
    timer_client = TimerClient(authorizer=authorizer, app_name="osprey-prototype")

    if flow_id != 2:
        run_input = {
            "osprey-worker-endpoint": user_endpoint,
            "download-function": Config.GLOBUS_FLOW_DOWNLOAD_FUNCTION,
            "database-commit-function": Config.GLOBUS_FLOW_COMMIT_FUNCTION,
            "user-wrapper-function": Config.GLOBUS_FLOW_USER_WRAPPER_FUNC,
            "tasks": json.dumps(
                [
                    {
                        "endpoint": user_endpoint,
                        "function": Config.GLOBUS_FLOW_DOWNLOAD_FUNCTION,
                        "kwargs": {"source_id": id},
                    }
                ]
            ),
            "author-email": email,
            "_private_password": os.environ.get("DSAAS_EMAIL_PASSWORD"),
        }
        run_label = f"Osprey Demo | Source {id}"
        name = f"osprey-demo-source-{id}"

    else:
        run_input = {
            "user_endpoint": kwargs["endpoint"],
            "user_function": kwargs["function"],
            "kwargs": json.dumps(kwargs["tasks"]),
        }
        run_label = "Osprey Demo | User flow"
        name = f"osprey-demo-user-flow-{id}"

    url = slash_join(sfc.base_url, f"/flows/{flow_id}/run")

    # TODO: TimerJob is now considered legacy.
    # run_as, run_monitor, run_manage all currently unsupported
    # ac = AuthClient(authorizer=authorizer)
    # user_uuid = ac.get_identities(usernames=email)["identities"][0]["id"]
    job = TimerJob(
        callback_url=url,
        callback_body={"body": run_input, "label": run_label},
        start=datetime.datetime.now(),
        interval=datetime.timedelta(seconds=interval_in_sec),
        name=name,
        scope=specific_flow_scope,
    )

    response = timer_client.create_job(job)
    assert response.http_status == 201
    job_id = response["job_id"]
    return job_id


def delete_job(job_id: str, flow_type: FlowEnum):
    flow_id = FLOW_IDS[flow_type]

    _ = SpecificFlowClient(flow_id=flow_id)
    authorizer, specific_flow_scope = create_authorizer(flow_id)
    timer_client = TimerClient(authorizer=authorizer, app_name="osprey-prototype")
    response = timer_client.delete_job(job_id=job_id)
    assert response.http_status == 200, response.http_reason


if __name__ == "__main__":
    flow_id = FLOW_IDS[FlowEnum.NONE]
    create_authorizer(flow_id)
