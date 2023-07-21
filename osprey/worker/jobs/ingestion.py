from sqlalchemy import select
from osprey.worker.models.database import Session
from osprey.worker.models.source import Source

def query_all_sources():
    statement = select(Source)
    with Session.begin() as session:
        result = session.execute(statement).all()
        return result