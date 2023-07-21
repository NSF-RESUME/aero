from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from osprey.worker.config import Config
from sqlalchemy.orm import declarative_base

Base = declarative_base()
engine = create_engine(Config.DATABASE_URL, pool_size=50, echo=False)
Session = sessionmaker(bind=engine)