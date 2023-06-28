from flask import Blueprint, jsonify, request
from app.models import Proxy

proxy_routes = Blueprint('proxy_routes', __name__, url_prefix='/proxies')

@proxy_routes.route('/', methods=['GET'])
def all_proxies():
    page        = request.args.get('page') or 1
    per_page    = request.args.get('per_page') or 15
    proxies     = Proxy.query.paginate(page=page, per_page=per_page)
    result      = [proxy.toJSON() for proxy in proxies]
    return jsonify(result), 200

@proxy_routes.route('/', methods=["POST"])
def create_proxy():
    return jsonify("Creating proxies!"), 200

@proxy_routes.route('/<id>', methods=["GET"])
def get_data(id):
    p = Proxy.query.get(id)
    if p is None:
        return jsonify({}), 404

    return jsonify(p.toJSON()), 200

