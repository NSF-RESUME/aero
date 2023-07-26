import datetime, os, sys

from osprey.server.lib.globus_compute import register_function
from globus_sdk import TimerClient
from globus_sdk import TimerJob
from globus_sdk.utils import slash_join
from osprey.server.lib.error import ServiceError, FLOW_TIMER_ERROR
from globus_sdk import SpecificFlowClient
from osprey.server.lib.globus_flow import create_authorizer

# Permanent
_FLOW_UUID: str = "6c2f7e41-00d0-4dc7-8c2b-2daea17edf2e"

def set_timer(interval_in_sec: int, name: str, id: int) -> None:
    """Set a Globus Timer for daily retrieval of updated tables from sources.

    Arguments:
        func_uuid: The Globus Compute registered function UUID.
    """
    func_uuid     = os.getenv('TIMER_FUNCTION_UUID')
    endpoint_uuid = os.getenv('TIMER_ENDPOINT_UUID')
    if func_uuid is None or endpoint_uuid is None:
        raise ServiceError(FLOW_TIMER_ERROR, 'Ensure that timer has both function and endpoint uuid')

    # client, sfc, timer_scope = create_context(_FLOW_UUID)
    sfc = SpecificFlowClient(flow_id=_FLOW_UUID)
    authorizer, specific_flow_scope = create_authorizer(_FLOW_UUID)
    timer_client = TimerClient(authorizer=authorizer, app_name="osprey-prototype")

    run_input = {"endpoint": endpoint_uuid, "function": func_uuid, 'args': [id]}
    run_label = f"Osprey Demo | Source {id}"

    url = slash_join(sfc.base_url, f"/flows/{_FLOW_UUID}/run")

    job = TimerJob(
        callback_url=url,
        callback_body={"body": run_input, "label": run_label},
        start=datetime.datetime.utcnow(),
        interval=datetime.timedelta(seconds=interval_in_sec),
        name=f"osprey-prototype-{name}",
        scope=specific_flow_scope,
    )

    response = timer_client.create_job(job)
    assert response.http_status == 201
    job_id = response["job_id"]
    return job_id

def scrape(id):
    from osprey.worker.models import Source
    from osprey.worker.models.database import Session
    with Session() as s:
        source = s.query(Source).get(id)
        # TODO: Error handle here
        source.check_new_version()

if __name__ == "__main__":
    if(len(sys.argv) != 2):
        print("Usage: python timer.py <endpoint_id>")
        exit()

    endpoint_uuid = sys.argv[1]
    func_uuid = register_function(scrape)
    # TODO: Fix this, maybe use `export`
    os.environ['TIMER_FUNCTION_UUID'] = func_uuid
    os.environ['TIMER_ENDPOINT_UUID'] = endpoint_uuid

    print(f"TIMER_FUNCTION_UUID: {func_uuid} \n | TIMER_ENDPOINT_UUID : {endpoint_uuid}")
