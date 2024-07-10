from globus_compute_sdk import Client
from globus_compute_sdk import Executor


def register_function(func):
    gcc = Client()
    func_uuid = gcc.register_function(func)
    return func_uuid


def execute_function(
    function_uuid: str, endpoint_uuid: str, *args, **kwargs
) -> tuple[list, dict]:
    with Executor(endpoint_id=endpoint_uuid) as gce:
        print("about to run")
        future = gce.submit_to_registered_function(
            function_uuid, args=args, kwargs=kwargs
        )
        return future.result()


if __name__ == "__main__":

    def temp():
        pass

    if register_function(temp):
        print("Done!")
