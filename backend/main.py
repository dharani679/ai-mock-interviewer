import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.config.settings import settings
from apps.db.init_db import init_db
from apps.routers.auth import router as auth_router
from apps.routers.health import router as health_router
from apps.routers.interviews import router as interviews_router
from apps.websocket.interviews import router as interview_websocket_router

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s",
)
logging.getLogger("apps").setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(interviews_router, prefix="/api/v1")
app.include_router(interview_websocket_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=1662, reload=True)
