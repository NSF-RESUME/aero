from contextlib import asynccontextmanager
from fastapi import FastAPI

from aero import GLOBUS_CLIENT
from aero.routers import data
from aero.routers import flow
from aero.routers import provenance

from aero.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()

    if GLOBUS_CLIENT.search_index is None:
        GLOBUS_CLIENT._create_search_idx()

    yield


# app = FastAPI(dependencies=[Depends(get_query_token)])
app = FastAPI(lifespan=lifespan)

app.include_router(data.router)
app.include_router(data.webhook_router)
app.include_router(flow.router)
app.include_router(provenance.router)
