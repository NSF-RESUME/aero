import logging

from sqlalchemy import inspect

from sqlmodel import create_engine
from sqlmodel import SQLModel
from sqlmodel import Session

from aero.config import Config

logger = logging.getLogger(__name__)

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

# Columns added to tables that already existed in deployed databases. create_all()
# creates missing *tables* but never alters existing ones, so on an upgraded database
# these have to be added by hand — and the failure is otherwise silent until a query
# hits them.
_REQUIRED_COLUMNS = {
    "data": ["no_copy"],
    "dataversion": ["source_key"],
}

_MIGRATION_SQL = """\
ALTER TABLE data        ADD COLUMN no_copy    boolean NOT NULL DEFAULT false;
ALTER TABLE dataversion ADD COLUMN source_key varchar;"""


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    check_schema()


def check_schema() -> list[str]:
    """Warn loudly about columns create_all() cannot add to pre-existing tables.

    Returns the list of missing "table.column" names (empty when the schema is good).
    """
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    missing = []
    for table, columns in _REQUIRED_COLUMNS.items():
        if table not in tables:
            continue  # create_all just built it, or it is genuinely absent
        present = {c["name"] for c in inspector.get_columns(table)}
        missing.extend(f"{table}.{c}" for c in columns if c not in present)

    if missing:
        logger.error(
            "Database schema is out of date — missing %s. create_all() cannot add "
            "columns to existing tables; apply this by hand (adminer) and restart:\n%s",
            ", ".join(missing),
            _MIGRATION_SQL,
        )

    return missing


def get_session():
    with Session(engine) as session:
        yield session
