from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.inbound.http.root_router import make_fastapi_root_router
from src.inbound.kafka.consumer import consumer
from src.main.config.logging import setup_logging
from src.main.config.settings import settings
from src.main.setup.background_tasks import BackgroundTaskRunner
from src.main.workers import BACKGROUND_WORKERS
from src.outbound.database.session import engine
from src.outbound.kafka.client import producer

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await producer.start()
    await consumer.start()

    background_tasks = BackgroundTaskRunner()
    background_tasks.start_all(BACKGROUND_WORKERS)

    yield

    await background_tasks.shutdown()
    await consumer.stop()
    await producer.stop()
    await engine.dispose()


app = FastAPI(
    title=settings.app.SERVICE_NAME,
    version="1.0.0",
    summary=f"OpenAPI schema for {settings.app.SERVICE_NAME}",
    root_path=settings.app.ROOT_PATH.rstrip("/"),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(make_fastapi_root_router(debug_mode=settings.app.DEBUG_MODE))
