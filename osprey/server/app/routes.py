from flask import Blueprint

all_routes = Blueprint('all_routes', __name__, url_prefix='/osprey/api/v1.0')
 
from osprey.server.routes.proxy import proxy_routes
from osprey.server.routes.source import source_routes
from osprey.server.routes.function import function_routes

all_routes.register_blueprint(proxy_routes)
all_routes.register_blueprint(source_routes)
all_routes.register_blueprint(function_routes)