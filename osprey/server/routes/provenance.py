from flask import Blueprint, jsonify, request
from osprey.server.app import db
from osprey.server.app.models import Provenance
from osprey.server.lib.error import ServiceError

provenance_routes = Blueprint('provenance_routes', __name__, url_prefix='/prov')

@provenance_routes.route('/', methods=['GET'])
def show_provenance():
    page        = request.args.get('page') or 1
    per_page    = request.args.get('per_page') or 15
    provs       = Provenance.query.paginate(page=page, per_page=per_page)
    result      = [p.toJSON() for p in provs]
    return jsonify(result), 200