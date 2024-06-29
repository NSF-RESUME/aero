from flask import Blueprint, jsonify, request

from osprey.server.app import db
from osprey.server.app import SEARCH_INDEX
from osprey.server.app.decorators import authenticated
from osprey.server.models.source import Source
from osprey.server.models.source_version import SourceVersion
from osprey.server.lib.globus_search import DSaaSSearchClient
from osprey.server.lib.error import ServiceError

source_routes = Blueprint("source_routes", __name__, url_prefix="/source")


@source_routes.route("/", methods=["GET"])
@authenticated
def all_sources():
    page = request.args.get("page") or 1
    per_page = request.args.get("per_page") or 15
    sources = Source.query.order_by(Source.id.desc()).paginate(
        page=page, per_page=per_page
    )
    result = [source.toJSON() for source in sources]
    return jsonify(result), 200


@source_routes.route("/search", methods=["GET"])
@authenticated
def search():
    query = request.args.get("query")
    sc = DSaaSSearchClient(SEARCH_INDEX).client

    try:
        result = sc.search(SEARCH_INDEX, query, advanced=True)
    except Exception as e:
        return jsonify(str(e)), 500
    return result.text, 200


@source_routes.route("/", methods=["POST"])
@authenticated
def create_source():
    try:
        json_data = request.json
        s = Source(**json_data)
        return jsonify(s.toJSON()), 200
    except ServiceError as s:
        return jsonify(s.toJSON()), s.code
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500


@source_routes.route("/<id>", methods=["GET"])
@authenticated
def get_data(id):
    s = db.session.get(Source, id)
    if s is None:
        return jsonify({"code": 404, "message": "Not found"}), 404

    return jsonify(s.toJSON()), 200


@source_routes.route("/<id>/versions", methods=["GET"])
@authenticated
def list_versions(id):
    s = db.session.get(Source, id)
    if s is None:
        return jsonify({"code": 404, "message": "Not found"}), 404

    return jsonify([v.toJSON() for v in s.versions]), 200


@source_routes.route("/<id>/file", methods=["GET"])
@authenticated
def grap_file(id):
    source = db.session.get(Source, id)
    if not source:
        return jsonify({"code": 404, "message": f"Source with id {id} not found"}), 404

    version = request.args.get("version")
    if not version:
        s = list(
            SourceVersion.query.filter(SourceVersion.source_id == id)
            .order_by(SourceVersion.version.desc())
            .limit(1)
        )
    else:
        s = list(
            SourceVersion.query.filter(SourceVersion.source_id == id)
            .filter(SourceVersion.version == version)
            .limit(1)
        )

    if len(s) == 0:
        return jsonify(
            {
                "code": 404,
                "message": f"Source with id {id} and version {version} not found",
            }
        ), 404

    return jsonify(s[0].toJSON()), 200


@source_routes.route("/<id>/new-version", methods=["POST"])
@authenticated
def add_version(id):
    source = db.session.get(Source, id)

    if not source:
        return jsonify({"code": 404, "message": f"Source with id {id} not found"}), 404

    try:
        json_data = request.json
        response = source.add_new_version(
            json_data["file"],
            json_data["file_format"],
            json_data["checksum"],
            json_data["size"],
        )
        return response
    except ServiceError as s:
        return jsonify(s.toJSON()), s.code
    except Exception as e:
        return jsonify({"code": 500, "message": str(e)}), 500
