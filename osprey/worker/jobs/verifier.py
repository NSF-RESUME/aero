from osprey.server.lib.globus_compute import execute_function, get_result
from osprey.worker.lib.serializer     import serialize, deserialize

"""

NOTE: Ideally our verifier should look like this 


def verifier(data: Proxy) -> bool:
    if all checks out
        return True
    
    return False

TODO:  'Discuss'

1. How to validate if the verifier is the same format when user submits
2. How to expose a default serialization function for the verfier? 
3. Should the serializer be part of the CLI ^^


"""

def verify(proxy, verifier):
    # NOTE: Assuming dill and codecs was used to serialize it
    # TODO: Extend it to use multiple serializers
    f = deserialize(verifier)
    try:
        return eval('f(proxy)') == True
    except Exception as e:
        return False

def verifier_microservice(data, verifier):
    """ Maybe use funcX to execute this? """
    if data is None:
        return False

    if verifier is not None:
        # TODO: Maybe use proxy for this?
        return verify(proxy=data, verifier=verifier)    # TODO: Use globus_compute

    return True


if __name__ == "__main__":
    # NOTE: Mocking 'def verifier_microservice()'
    def temp_verifier(data) -> bool:
        return sum(data) == 15

    serialized_function = serialize(temp_verifier) # Assume this is retrived from the database
    assert verify([1,2,3,4,5], serialized_function)