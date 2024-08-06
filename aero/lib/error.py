class ServiceError(Exception):
    def __init__(self, code, message, **kwargs):
        self.code = code
        self.message = message
        super().__init__(**kwargs)

    def __str__(self) -> str:  # pragma: no cover
        return f"Error {self.code} : {self.message}"

    def toJSON(self) -> dict:
        return {"code": self.code, "message": self.message}


MODEL_INSUFFICIENT_ATTRS = 601
FLOW_TIMER_ERROR = 602
PROXYIFY_ERROR = 603
FILE_NOT_FOUND = 604
SERIALIZE_ERR = 605
DESERIALIZE_ERR = 606
CUSTOM_FUNCTION_ERROR = 607
