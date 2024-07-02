from flask import Blueprint, jsonify, request

from osprey.server.app.decorators import authenticated
from osprey.server.models.output import Output

output_routes = Blueprint("output_routes", __name__, url_prefix="/output")


@output_routes.route("/", methods=["GET"])
@authenticated
def show_output():
    page = request.args.get("page") or 1
    per_page = request.args.get("per_page") or 15
    outputs = Output.query.order_by(Output.id.desc()).paginate(
        page=page, per_page=per_page
    )
    result = [o.toJSON() for o in outputs]
    return jsonify(result), 200


@output_routes.route("/new", methods=["POST"])
@authenticated
def create_output_file():
    data = request.json

    assert "filename" in data
    assert "checksum" in data
    assert "url" in data
    assert "name" in data

    if "description" not in data:
        data["description"] = None

    o: Output = Output(name=data["name"], url=data["url"])
    o.add_new_version(filename=data["filename"], checksum=data["checksum"])
    return jsonify(o.toJSON()), 200
