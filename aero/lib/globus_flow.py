from globus_sdk import TimerClient

from aero.lib.utils import _flow_scopes
from aero.lib.globus_auth import get_authorizer


def create_client(scopes):
    authorizer = get_authorizer(scopes=scopes)
    return TimerClient(authorizer=authorizer, app_name="osprey-prototype")


def get_job(job_id):
    timer_client = create_client(scopes=_flow_scopes())
    return timer_client.get_job(job_id)
