from flask import Blueprint, jsonify, request
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
