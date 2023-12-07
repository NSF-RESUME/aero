import datetime
import json
import os

from osprey.server.lib.globus_compute import register_function
from globus_sdk import AuthClient
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
USER_FLOW_UUID = '0d8ace1a-d583-4f65-834e-4e1e1f450ecc'
USER_ENDPOINT_UUID = '1fd89678-3c6f-4bac-8e2b-306da6004b13'

def set_timer(interval_in_sec: int, id: int, email: str, flow_type: FlowEnum) -> None:
    """Set a Globus Timer for daily retrieval of updated tables from sources.

    Arguments:
        func_uuid: The Globus Compute registered function UUID.
    """
    flow_id       = FLOW_IDS[flow_type]

    sfc = SpecificFlowClient(flow_id=flow_id)
    authorizer, specific_flow_scope = create_authorizer(flow_id)
    timer_client = TimerClient(authorizer=authorizer, app_name="osprey-prototype")

    if flow_id != 2:
        run_input = {
                    "osprey-worker-endpoint": Config.GLOBUS_WORKER_UUID,
                    "download-function": Config.GLOBUS_FLOW_DOWNLOAD_FUNCTION, 
                    "database-commit-function": Config.GLOBUS_FLOW_COMMIT_FUNCTION,
                    "user-wrapper-function": Config.GLOBUS_FLOW_USER_WRAPPER_FUNC,
                    "tasks": json.dumps([{
                        "endpoint": Config.GLOBUS_WORKER_UUID,
                        "function": Config.GLOBUS_FLOW_DOWNLOAD_FUNCTION,
                        "kwargs": {
                            "source_id": id
                        }}]),
                    "author-email": email,
                    "_private_password": os.environ.get('DSAAS_EMAIL_PASSWORD') 
                    }
        run_label = f"Osprey Demo | Source {id}"
        
    else:
        run_input = {
            "endpoint": USER_ENDPOINT_UUID,
            "function": USER_FLOW_UUID
        }
        run_label = f'Osprey Demo | User flow'

    url = slash_join(sfc.base_url, f"/flows/{flow_id}/run")
    
    # TODO: TimerJob is now considered legacy.
    try:
        ac = AuthClient(...)
        user_uuid = ac.get_identities(email)
        job = TimerJob(
            callback_url=url,
            callback_body={"body": run_input, "label": run_label},
            start=datetime.datetime.utcnow(),
            interval=datetime.timedelta(seconds=interval_in_sec),
            name=f"osprey-demo-source-{id}",
            scope=specific_flow_scope,
            monitor_by=user_uuid,
        )
    except Exception as e: # AuthAPIError
        job = TimerJob(
            callback_url=url,
            callback_body={"body": run_input, "label": run_label},
            start=datetime.datetime.utcnow(),
            interval=datetime.timedelta(seconds=interval_in_sec),
            name=f"osprey-demo-source-{id}",
            scope=specific_flow_scope,
        )
        print(e) # TODO: replace by a logger


    response = timer_client.create_job(job)
    assert response.http_status == 201
    job_id = response["job_id"]
    return job_id

if __name__ == "__main__":
    flow_id = FLOW_IDS[FlowEnum.NONE]
    create_authorizer(flow_id)