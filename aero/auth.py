from flask import request

from aero import GLOBUS_CLIENT
from aero.error_handler import UnauthorizedError
from aero.error_handler import ForbiddenError


def is_token_valid():
    if "Authorization" not in request.headers:
        raise UnauthorizedError()

    # Get the access token from the request
    token = request.headers["Authorization"].split(" ")[1]

    # Call token introspect
    token_meta = GLOBUS_CLIENT.auth_client.oauth2_token_introspect(token)

    if not token_meta.get("active"):
        raise ForbiddenError()

    # todo: unnecessary
    # Token has passed verification so we attach it to the
    # request global object and proceed
    # g.req_token = token

    return True


# def authenticated(fn):
#     """Mark a route as requiring authentication."""

#     @wraps(fn)
#     def decorated_function(*args, **kwargs):
#         if is_token_valid():
#             return fn(*args, **kwargs)

#     return decorated_function
