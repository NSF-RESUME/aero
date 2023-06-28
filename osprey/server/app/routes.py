from flask import Blueprint
from routes.proxy import proxy_routes
from routes.source import source_routes

all_routes = Blueprint('all_routes', __name__, url_prefix='/osprey/api/v1.0')

all_routes.register_blueprint(proxy_routes)
all_routes.register_blueprint(source_routes)