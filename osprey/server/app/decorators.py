from flask import g, request
from functools import wraps

from osprey.server.app.error_handler import UnauthorizedError
from osprey.server.app.error_handler import ForbiddenError
from osprey.server.app.utils import get_token
from osprey.server.app.utils import load_auth_client

# from service import app
# from service.errors import (BadRequestError, UnauthorizedError, ForbiddenError,
#                             InternalServerError)
# from service.utils import load_auth_client, get_token


def authenticated(fn):
    """Mark a route as requiring authentication."""

    @wraps(fn)
    def decorated_function(*args, **kwargs):
        if "Authorization" not in request.headers:
            raise UnauthorizedError()

        # Get the access token from the request
        token = get_token(request.headers["Authorization"])

        # Call token introspect
        client = load_auth_client()
        token_meta = client.oauth2_token_introspect(token)

        if not token_meta.get("active"):
            raise ForbiddenError(token_meta)

        # todo: unnecessary
        # Token has passed verification so we attach it to the
        # request global object and proceed
        g.req_token = token

        return fn(*args, **kwargs)

    return decorated_function
