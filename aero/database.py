from sqlmodel import create_engine
from sqlmodel import SQLModel
from sqlmodel import Session

from aero.config import Config

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
