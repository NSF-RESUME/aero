from globus_compute_sdk import Client

gcc = Client()

def register_function(func):
    func_uuid = gcc.register_function(func)
    return func_uuid

def execute_function(function_uuid: str, endpoint_uuid: str) -> str:
    tracker_uuid = gcc.run(function_id=function_uuid, endpoint_id=endpoint_uuid)
    return tracker_uuid

def get_result(tracker_uuid : str):
    result = gcc.get_result(tracker_uuid)
    return result