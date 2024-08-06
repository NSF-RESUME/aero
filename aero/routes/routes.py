from flask import Blueprint

# from osprey.server.routes.proxy import proxy_routes
from aero.routes.source import source_routes
from aero.routes.output import output_routes
from aero.routes.provenance import provenance_routes

all_routes = Blueprint("all_routes", __name__, url_prefix="/osprey/api/v1.0")

# all_routes.register_blueprint(proxy_routes)
all_routes.register_blueprint(source_routes)
all_routes.register_blueprint(output_routes)
all_routes.register_blueprint(provenance_routes)
