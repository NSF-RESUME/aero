from flask import g, request
from functools import wraps

from aero.app.error_handler import UnauthorizedError
from aero.app.error_handler import ForbiddenError
from aero.app.utils import get_token
from aero.app.utils import load_auth_client


def is_token_valid():
    if "Authorization" not in request.headers:
        raise UnauthorizedError()

    # Get the access token from the request
    token = get_token(request.headers["Authorization"])

    # Call token introspect
    client = load_auth_client()
    token_meta = client.oauth2_token_introspect(token)

    if not token_meta.get("active"):
        raise ForbiddenError()

    # todo: unnecessary
    # Token has passed verification so we attach it to the
    # request global object and proceed
    g.req_token = token

    return True


def authenticated(fn):
    """Mark a route as requiring authentication."""

    @wraps(fn)
    def decorated_function(*args, **kwargs):
        if is_token_valid():
            return fn(*args, **kwargs)

    return decorated_function
