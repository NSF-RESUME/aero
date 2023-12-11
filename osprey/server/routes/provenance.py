from flask import Blueprint, jsonify, request
from osprey.server.app import db
from osprey.server.app.models import Function
from osprey.server.app.models import Output
from osprey.server.app.models import Provenance
from osprey.server.app.models import SourceVersion
from osprey.server.lib.error import ServiceError

provenance_routes = Blueprint('provenance_routes', __name__, url_prefix='/prov')

@provenance_routes.route('/', methods=['GET'])
def show_provenance():
    page        = request.args.get('page') or 1
    per_page    = request.args.get('per_page') or 15
    provs       = Provenance.query.paginate(page=page, per_page=per_page)
    result      = [p.toJSON() for p in provs]
    return jsonify(result), 200

@provenance_routes.route('/new/<function_id>', methods=['POST'])
def record_provenance(function_id):
    try:
        json_data = request.json

        assert 'output_id' in json_data

        sources: dict[int, int] = json_data['sources']
        source_ver: list[SourceVersion] = []
    
        # currently just gets last version
        for k,v in sources:
            SourceVersion(version=1, source_id=v)
            source_ver.append(SourceVersion.query.filter(SourceVersion.source_id == int(v)).order_by(SourceVersion.version.desc()).first())

        f = Function(uuid=function_id)
        o = Output(name=json_data['name'], filename=json_data['filename'])

        p = Provenance(function_id=f.id, derived_from=source_ver, contributed_to=[o], description=json_data['description'], function_args=json_data['args'])
    
        return jsonify(p.toJSON()), 200
        raise KeyError(source_ver)
    except ServiceError as s:
        return jsonify(p.toJSON()), s.code
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500
     