from config import Config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db)

# Insert routes here
# from app.posts import bp as posts_bp
# app.register_blueprint(posts_bp, url_prefix='/posts')

from app import models, routes

app.register_blueprint(routes.all_routes)