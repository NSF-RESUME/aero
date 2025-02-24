from contextlib import asynccontextmanager
from fastapi import FastAPI

from aero.routers import data
from aero.routers import flow
from aero.routers import provenance

from aero.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


# app = FastAPI(dependencies=[Depends(get_query_token)])
app = FastAPI(lifespan=lifespan)

app.include_router(data.router)
app.include_router(flow.router)
app.include_router(provenance.router)


# if __name__ == "__main__":
#     ssl_dir = Path(__file__).parent.parent / "ssl"
#     cert = ssl_dir / "cert.pem"
#     key = ssl_dir / "key.pem"
#     app.run(
#         host="0.0.0.0", port="80", ssl_context="adhoc", debug=True
#     )  # ssl_context=(cert, key), debug=True)
