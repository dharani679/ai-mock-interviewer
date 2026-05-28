from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.config.settings import settings
from apps.db.init_db import init_db
from apps.routers.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.include_router(health_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("apps.main:app", host="0.0.0.0", port=1662, reload=True)
