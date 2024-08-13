from flask import Blueprint

# from osprey.server.routes.proxy import proxy_routes
from aero.routes.data import data_routes
from aero.routes.flow import flow_routes

all_routes = Blueprint("all_routes", __name__, url_prefix="/osprey/api/v1.0")

# all_routes.register_blueprint(proxy_routes)
all_routes.register_blueprint(data_routes)
all_routes.register_blueprint(flow_routes)
