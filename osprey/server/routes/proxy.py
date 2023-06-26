from flask import Blueprint, jsonify

proxy_routes = Blueprint('proxy_routes', __name__, url_prefix='/proxies')

@proxy_routes.route('/', methods=['GET'])
def all_proxies():
    result = []
    return jsonify(result), 200

@proxy_routes.route('/', methods=["POST"])
def create_proxy():
    return jsonify("Creating proxies!"), 200

@proxy_routes.route('/<id>', methods=["GET"])
def get_data(id):
    return jsonify("Getting data!"), 200
