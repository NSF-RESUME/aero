import uuid
import os

from pathlib import Path

from flask import Blueprint, jsonify, request

from osprey.server.app.decorators import authenticated
from osprey.server.app.models import Output

output_routes = Blueprint("output_routes", __name__, url_prefix="/output")

if (test := os.getenv("DSAAS_TESTENV")) is not None and int(test) == 1:
    GCS_DIR = Path(Path.cwd(), "dsaas_storage", "output")
else:
    GCS_DIR = Path("/dsaas_storage/output")

# TODO: Just create these directories when GCS is created
GCS_DIR.mkdir(parents=True, exist_ok=True)


@output_routes.route("/", methods=["GET"])
@authenticated
def show_output():
    page = request.args.get("page") or 1
    per_page = request.args.get("per_page") or 15
    outputs = Output.query.paginate(page=page, per_page=per_page)
    result = [o.toJSON() for o in outputs]
    return jsonify(result), 200


@output_routes.route("/new", methods=["POST"])
@authenticated
def create_output_file():
    filename = str(uuid.uuid4())
    filepath = Path(GCS_DIR, filename)
    filepath.touch()

    return jsonify({"file": str(filepath)}), 200
