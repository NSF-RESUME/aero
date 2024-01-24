import os

from flask import Flask

from osprey.server.app.extensions import db
from osprey.server.config import Config
from flask_migrate import Migrate

SEARCH_INDEX = os.getenv("SEARCH_INDEX")


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)

    migrate = Migrate()

    migrate.init_app(app, db)
    # Initialize Flask extensions here

    # Register blueprints here
    from osprey.server.app.routes import all_routes

    app.register_blueprint(all_routes)

    return app
