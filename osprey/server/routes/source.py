from flask import Blueprint, jsonify, request, send_file
from osprey.server.app import db
from osprey.server.app.models import Source, SourceVersion
from osprey.server.lib.error import ServiceError

source_routes = Blueprint('source_routes', __name__, url_prefix='/source')

@source_routes.route('/', methods=['GET'])
def all_sources():
    page        = request.args.get('page') or 1
    per_page    = request.args.get('per_page') or 15
    sources     = Source.query.paginate(page=page, per_page=per_page)
    result      = [source.toJSON() for source in sources]
    return jsonify(result), 200

@source_routes.route('/', methods=['POST'])
def create_source():
    try:
        json_data = request.json
        s = Source(**json_data)
        return jsonify(s.toJSON()), 200
    except ServiceError as s:
        return jsonify(s.toJSON()), s.code
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

@source_routes.route('/<id>', methods=['GET'])
def get_data(id):
    s = Source.query.get(id)
    if s is None:
        return jsonify({'code': 404, 'message': 'Not found'}), 404

    return jsonify(s.toJSON()), 200

@source_routes.route('/<id>/versions', methods=['GET'])
def list_versions(id):
    s = Source.query.get(id)
    if s is None:
        return jsonify({'code': 404, 'message': 'Not found'}), 404

    return jsonify([v.toJSON() for v in s.versions]), 200

@source_routes.route('/<id>/file', methods=['GET'])
def grap_file(id):
    source = Source.query.get(id)
    if not source:
        return jsonify({'code': 404, 'message': f'Source with id {id} not found'}), 404

    version = request.args.get('version')
    if not version:
        s = list(SourceVersion.query.filter(SourceVersion.source_id == id).order_by(SourceVersion.version.desc()).limit(1))
    else:
        s = list(SourceVersion.query.filter(SourceVersion.source_id == id).filter(SourceVersion.version == version).limit(1))

    if len(s) == 0:
        return jsonify({'code': 404, 'message': f'Source with id {id} and version {version} not found'}), 404

    return jsonify(s[0].source_file.toJSON()), 200