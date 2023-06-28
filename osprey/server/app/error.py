
class ServiceError(Exception):
    def __init__(self, code, message, **kwargs):
        self.code    = code
        self.message = message
        super().__init__(**kwargs)
    
    def __str__(self) -> str:
        return f"Error {self.code} : {self.message}"

    def toJSON(self) -> dict:
        return {'code': self.code, 'message': self.message}
    
MODEL_INSUFFICIENT_ATTRS = 601
SERIALIZATION_ERROR      = 700
DESERIALIZATION_ERROR    = 701