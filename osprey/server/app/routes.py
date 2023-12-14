from flask import Blueprint

# from osprey.server.routes.proxy import proxy_routes
from osprey.server.routes.source import source_routes
from osprey.server.routes.function import function_routes
from osprey.server.routes.output import output_routes
from osprey.server.routes.provenance import provenance_routes

all_routes = Blueprint("all_routes", __name__, url_prefix="/osprey/api/v1.0")

# all_routes.register_blueprint(proxy_routes)
all_routes.register_blueprint(source_routes)
all_routes.register_blueprint(function_routes)
all_routes.register_blueprint(output_routes)
all_routes.register_blueprint(provenance_routes)
