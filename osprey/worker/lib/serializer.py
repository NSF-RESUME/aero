import pickle, dill, codecs
from osprey.worker.lib.error import ServiceError, DESERIALIZATION_ERROR, SERIALIZATION_ERROR, ENCODING_ERROR, DECODING_ERROR


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


def encode(data, format: str) -> str:
    if format == 'json':
        return pickle.dumps(data)

    if format == 'csv':
        return data.encode()

    raise ServiceError(ENCODING_ERROR, message="Cannot prepare data for database blob")

def decode(data, format: str) -> str:
    if format == 'json':
        return pickle.loads(data)

    if format == 'csv':
        return data.decode()

    raise ServiceError(DECODING_ERROR, message="Cannot prepare data for database blob")