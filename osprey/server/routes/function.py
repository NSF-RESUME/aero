from flask import Blueprint, jsonify, request

from osprey.server.lib.error import ServiceError
from osprey.server.models.function import Function
from osprey.server.models.provenance import Provenance
from osprey.server.models.output import Output
from osprey.server.models.source_version import SourceVersion
from osprey.server.lib.globus_compute import register_function
from osprey.server.lib.serializer import deserialize

function_routes = Blueprint('function_routes', __name__, url_prefix='/function')

@function_routes.route('/', methods=['GET'])
def register():
    function_string = request.args.get('function')
    if function_string is None:
        return jsonify({'code': 406, 'message': 'Needs `function` as argument'}), 406

    try:
        f = deserialize(function_string)
        f_id = register_function(f)
    except Exception as e:
        return jsonify({'code': 406, 'message': str(e)}), 406

    return jsonify({'code': 200, 'function_id': f_id}), 200

@function_routes.route('/<function_id>', methods=['POST'])
def record_provenance(function_id):
    try:
        json_data = request.json

        assert 'output_id' in json_data

        sources: list[tuple[str, str]] = []
        source_ver: list[SourceVersion] = []
        for k,v in json_data.items():
            if 'dsaas' in k:
                sources.append((k,v))
    
        # currently just gets last version
        for k,v in sources:
            SourceVersion(version=1, source_id=v)
            source_ver.append(SourceVersion.query.filter(SourceVersion.source_id == int(v)).order_by(SourceVersion.version.desc()).first())

        f = Function(uuid='1234')
        o = Output()

        p = Provenance(function_id=f.id, derived_from=source_ver, contributed_to=[o])
    
        return jsonify(p.toJSON()), 200
        raise KeyError(source_ver)
    except ServiceError as s:
        return jsonify(p.toJSON()), s.code
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500

    
