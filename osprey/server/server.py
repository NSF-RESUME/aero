from flask import jsonify

from osprey.server.app import db
from osprey.server.app import create_app
from osprey.server.app.models import (
    Source,
    SourceVersion,
    Proxy,
    Tag,
    Provenance,
    Function,
    SourceFile,
)
from osprey.server.app.error_handler import BadRequestError
from osprey.server.app.error_handler import ForbiddenError
from osprey.server.app.error_handler import InternalServerError
from osprey.server.app.error_handler import UnauthorizedError

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "Source": Source,
        "SourceVersion": SourceVersion,
        "proxy": Proxy,
        "tag": Tag,
        "provenance": Provenance,
        "function": Function,
        "SourceFile": SourceFile,
    }


@app.errorhandler(404)
def not_found_error(error):
    return jsonify(
        {"status": 404, "message": "Cannot find the page you are looking for"}
    ), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({"status": 404, "message": "Unexpected error has occurred"}), 500


@app.errorhandler(ForbiddenError)
def handle_forbidded_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code

    return response


@app.errorhandler(BadRequestError)
def handle_badrequest_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code

    return response


@app.errorhandler(InternalServerError)
def handle_internalserver_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code

    return response


@app.errorhandler(UnauthorizedError)
def handle_unauthorized_error(error):
    response = jsonify(error.to_dict())
    response.headers[
        "WWW-Authenticate"
    ] = 'Bearer realm="urn:globus:auth:scope:demo-resource-server:all"'
    response.status_code = error.status_code

    return response
