import os

class Config(object):
    DATABASE_HOST              = os.getenv('DATABASE_HOST')
    DATABASE_USER              = os.getenv('DATABASE_USER')
    DATABASE_PASSWORD          = os.getenv('DATABASE_PASSWORD')
    PORT                       = os.getenv('DATABASE_PORT')
    DATABASE_NAME              = os.getenv('DATABASE_NAME')
    GLOBUS_WORKER_UUID         = os.getenv('GLOBUS_WORKER_UUID')
    PROXYSTORE_ENDPOINT_UUID   = os.getenv('PROXYSTORE_ENDPOINT_UUID')
    GLOBUS_FLOW_DOWNLOAD_FUNCTION = os.getenv('GLOBUS_FLOW_DOWNLOAD_FUNCTION')
    GLOBUS_FLOW_COMMIT_FUNCTION   = os.getenv('GLOBUS_FLOW_COMMIT_FUNCTION')
    GLOBUS_FLOW_USER_WRAPPER_FUNC = os.getenv('GLOBUS_FLOW_USER_COMMIT_FUNCTION')
    SQLALCHEMY_DATABASE_URI    = f'postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{PORT}/{DATABASE_NAME}'
    GCS_ENDPOINT_ID            = os.getenv('GCS_ENDPOINT_UUID')
    CLIENT_ID                  = os.getenv('FUNCX_SDK_CLIENT_ID')
    CLIENT_SECRET              = os.getenv('FUNCX_SDK_CLIENT_SECRET')
    GCS_MANAGER_DOMAIN_NAME    = os.getenv('GCS_MANAGER_DOMAIN_NAME')
    STORAGE_GATEWAY_ID         = os.getenv('GCS_STORAGE_GATEWAY_ID')
    MAPPED_COLLECTION_ID       = os.getenv('GCS_MAPPED_COLLECTION_ID')
    SERVICE_USER               = os.getenv('GCS_SERVICE_USER')
    CONNECTOR_ID               = os.getenv('CONNECTOR_ID')
    SQLALCHEMY_TRACK_MODIFICATIONS = False