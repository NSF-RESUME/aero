from globus_compute_sdk import Client

def register_function(func):
    gcc = Client()
    func_uuid = gcc.register_function(func)
    return func_uuid

def execute_function(function_uuid: str, endpoint_uuid: str, *args, **kwargs) -> str:
    gcc = Client()
    tracker_uuid = gcc.run(*args, **kwargs, function_id=function_uuid, endpoint_id=endpoint_uuid)
    return tracker_uuid

# TODO: Get @Valerie to review this
def get_result(tracker_uuid : str, block: bool = False):
    gcc = Client()
    first_attempt = True
    result = None
    while block or first_attempt:
        try:
            result = gcc.get_result(tracker_uuid)
            break
        except Exception as e:
            first_attempt = False
            continue # NOTE: How do i know the function result was not the exception??

    return result
