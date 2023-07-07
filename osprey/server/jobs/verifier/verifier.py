from app.models import Source
from app.error import ServiceError, DESERIALIZATION_ERROR, SERIALIZATION_ERROR
import dill
import codecs

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

def serialize(obj) -> str:
    """
        Takes a function and returns a serialized string
    """
    try:
        return codecs.encode(dill.dumps(obj), "base64").decode()
    except Exception:
        raise ServiceError(code=SERIALIZATION_ERROR, message="Cannot serialize verifier")


def deserialize(obj: str):
    """
        Takes a string and returns a function
    """
    try:
        return dill.loads(codecs.decode(obj.encode(), "base64"))
    except Exception:
        raise ServiceError(code=DESERIALIZATION_ERROR, message="Cannot deserailize verifier")
    

""" Maybe use funcX to execute this? """
def verify(proxy, verifier):
    f = deserialize(verifier)
    try:
        return eval('f(proxy)') == True
    except Exception as e:
        return False

def verifier_microservice(source_id):
    source = Source.query.get(source_id)
    print(source)
    if source is not None and source.verifier is not None:
        # NOTE: Assuming dill and codecs was used to serialize it
        # TODO: Extend it to use multiple serializers

        proxy = None # Get proxy for the source?? # NOTE: Change this
        return verify(proxy, source.verifier)

    return True


if __name__ == "__main__":
    # NOTE: Mocking 'def verifier_microservice()'
    def temp_verifier(data) -> bool:
        return sum(data) == 15

    serialized_function = serialize(temp_verifier) # Assume this is retrived from the database
    assert verify([1,2,3,4,5], serialized_function)