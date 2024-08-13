from flask import Blueprint, jsonify, request

from aero.app import db
from aero.app.decorators import authenticated
from aero.app.utils import get_search_client
from aero.models.data import Data
from aero.models.data_version import DataVersion
from aero.globus.error import ServiceError

data_routes = Blueprint("data_routes", __name__, url_prefix="/data")


@data_routes.route("/", methods=["GET"])
@authenticated
def all_sources():
    page = request.args.get("page") or 1
    per_page = request.args.get("per_page") or 15
    sources = Data.query.order_by(Data.id.desc()).paginate(page=page, per_page=per_page)
    result = [source.toJSON() for source in sources]
    return jsonify(result), 200


@data_routes.route("/search", methods=["GET"])
@authenticated
def search():
    query = request.args.get("query")
    sc = get_search_client()

    try:
        result = sc.client.search(sc.index, query, advanced=True)
    except Exception as e:
        return jsonify(str(e)), 500
    return result.text, 200


@data_routes.route("/", methods=["POST"])
@authenticated
def create_source():
    try:
        json_data = request.json
        s = Data(**json_data)
        return jsonify(s.toJSON()), 200
    except ServiceError as s:
        return jsonify(s.toJSON()), s.code
    except Exception as e:  # pragma: no cover
        return jsonify({"code": 500, "message": str(e)}), 500


@data_routes.route("/<id>", methods=["GET"])
@authenticated
def get_data(id):
    s = db.session.get(Data, id)
    if s is None:
        return jsonify({"code": 404, "message": "Not found"}), 404

    return jsonify(s.toJSON()), 200


@data_routes.route("/<id>/versions", methods=["GET"])
@authenticated
def list_versions(id):
    s = db.session.get(Data, id)
    if s is None:
        return jsonify({"code": 404, "message": "Not found"}), 404

    return jsonify([v.toJSON() for v in s.versions]), 200


@data_routes.route("/<id>/file", methods=["GET"])
@authenticated
def grap_file(id):
    source = db.session.get(Data, id)
    if not source:
        return jsonify({"code": 404, "message": f"Data with id {id} not found"}), 404

    version = request.args.get("version")
    if not version:
        s = list(
            DataVersion.query.filter(DataVersion.data_id == id)
            .order_by(DataVersion.version.desc())
            .limit(1)
        )
    else:
        s = list(
            DataVersion.query.filter(DataVersion.data_id == id)
            .filter(DataVersion.version == version)
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


@data_routes.route("/<id>/new-version", methods=["POST"])
@authenticated
def add_version(id):
    source = db.session.get(Data, id)

    if not source:
        return jsonify({"code": 404, "message": f"Source with id {id} not found"}), 404

    try:
        json_data = request.json
        response = source.add_new_version(
            json_data["file"],
            json_data["file_format"],
            json_data["checksum"],
            json_data["size"],
            json_data["encoding"] if "encoding" in json_data else None,
        )
        return response
    except ServiceError as s:  # pragma: no cover
        return jsonify(s.toJSON()), s.code
    except Exception as e:  # pragma: no cover
        return jsonify({"code": 500, "message": str(e)}), 500
