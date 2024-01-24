import os

os.environ["DATABASE_HOST"] = "127.0.0.1"
os.environ["DATABASE_USER"] = "postgres"
os.environ["DATABASE_PASSWORD"] = "postgres"
os.environ["DATABASE_PORT"] = "5001"
os.environ["DATABASE_NAME"] = "osprey_development"
# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate

# #from osprey.server.app import routes

# import pytest

# #TODO: replace app __init__.py with a `create_app` function and remove boilerplate code
# @pytest.fixture()
# def app():
#     DATABASE_PORT=5432
#     DATABASE_PASSWORD='postgres'
#     DATABASE_USER='postgres'
#     DATABASE_HOST='127.0.0.1' #'osprey-postgres-database-1'
#     DATABASE_NAME='osprey_development'

#     config = {
#         'DATABASE_HOST': DATABASE_HOST,
#         'DATABASE_USER': DATABASE_USER,
#         'DATABASE_PASSWORD': DATABASE_PASSWORD,
#         'PORT': DATABASE_PORT,
#         'DATABASE_NAME': DATABASE_NAME,
#         'SQLALCHEMY_DATABASE_URI' : f'postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}'
#     }
#     from osprey.server.app import app
#     # db = SQLAlchemy()
#     # migrate = Migrate()
#     # app = Flask(__name__)

#     # app.config.from_mapping(config)

#     # db.init_app(app)
#     # migrate.init_app(app, db)

#     # app.register_blueprint(routes.all_routes)
#     app.config.update(config)

#     yield app

# @pytest.fixture
# def client(app):
#     return app.test_client()
