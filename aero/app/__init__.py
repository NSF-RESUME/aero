from flask import Flask

from aero.app.extensions import db
from aero.config import Config
from flask_migrate import Migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)

    migrate = Migrate()

    migrate.init_app(app, db)
    # Initialize Flask extensions here

    # Register blueprints here
    from aero.app.routes import all_routes

    app.register_blueprint(all_routes)

    return app
