from aero.app import error_handler


def test_forbidden():
    eh = error_handler.ForbiddenError()

    assert eh.message is not None and eh.status_code == 403 and eh.payload is None

    ret = eh.to_dict()
    assert list(ret.keys()) == ["message"]
    assert ret["message"] == "Permission Denied"

    message = "test"
    status_code = 100
    eh = error_handler.ForbiddenError(message=message, status_code=status_code)
    assert eh.message == message and eh.status_code == status_code


def test_unauthorized():
    eh = error_handler.UnauthorizedError()
    assert eh.message is not None and eh.status_code == 401 and eh.payload is None

    ret = eh.to_dict()
    assert list(ret.keys()) == ["message"]
    assert ret["message"] == "Not Authorized"

    message = "test"
    status_code = 100
    eh = error_handler.UnauthorizedError(message=message, status_code=status_code)
    assert eh.message == message and eh.status_code == status_code
