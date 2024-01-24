import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

from globus_sdk import SearchClient

from osprey.server.lib.globus_search import create_authorizer
from osprey.worker.config import Config

Base = declarative_base()
engine = create_engine(Config.DATABASE_URL, pool_size=50, echo=False)
Session = sessionmaker(bind=engine)

SEARCH_INDEX = os.getenv("SEARCH_INDEX")
authorizer = create_authorizer()
search_client = SearchClient(authorizer=authorizer)
