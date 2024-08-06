from flask import Blueprint, jsonify, request

from aero.app import db
from aero.app.decorators import authenticated
from aero.models.output import Output
from aero.models.output_version import OutputVersion

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
    assert "collection_uuid" in data

    if "description" not in data:
        data["description"] = None

    o: Output = Output(
        name=data["name"], url=data["url"], collection_uuid=data["collection_uuid"]
    )
    o.add_new_version(filename=data["filename"], checksum=data["checksum"])
    return jsonify(o.toJSON()), 200


@output_routes.route("/<id>/file", methods=["GET"])
@authenticated
def grap_file(id):
    source = db.session.get(Output, id)
    if not source:
        return jsonify({"code": 404, "message": f"Source with id {id} not found"}), 404

    version = request.args.get("version")
    if not version:
        s = list(
            OutputVersion.query.filter(OutputVersion.output_id == id)
            .order_by(OutputVersion.version.desc())
            .limit(1)
        )
    else:
        s = list(
            OutputVersion.query.filter(OutputVersion.output_id == id)
            .filter(OutputVersion.version == version)
            .limit(1)
        )

    if len(s) == 0:
        return jsonify(
            {
                "code": 404,
                "message": f"Output with id {id} and version {version} not found",
            }
        ), 404

    return jsonify(s[0].toJSON()), 200
