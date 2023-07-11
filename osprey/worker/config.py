import os

class Config(object):
    DATABASE_HOST     = os.getenv('DATABASE_HOST')
    DATABASE_USER     = os.getenv('DATABASE_USER')
    DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')
    PORT              = os.getenv('DATABASE_PORT')
    DATABASE_NAME     = os.getenv('DATABASE_NAME')
    DATABASE_URL      = f'postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{PORT}/{DATABASE_NAME}'