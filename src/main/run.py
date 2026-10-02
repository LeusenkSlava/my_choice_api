from contextlib import asynccontextmanager
from functools import partial

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.inbound.http.root_router import make_fastapi_root_router
from src.inbound.kafka.consumer import build_consumer
from src.inbound.kafka.tasks.consume_loop import consume_loop
from src.main.config.logging import setup_logging
from src.main.config.settings import settings
from src.main.setup.background_tasks import BackgroundTaskRunner
from src.outbound.ai_plot.client import build_ai_plot_client
from src.outbound.ai_plot.tasks.generation_job_relay_worker import (
    run_generation_job_relay_worker,
)
from src.outbound.database.session import engine
from src.outbound.kafka.client import build_producer
from src.outbound.kafka.publishers.generation_job import KafkaGenerationJobPublisher

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    producer = build_producer()
    await producer.start()
    consumer = build_consumer()
    await consumer.start()
    app.state.ai_plot_client = build_ai_plot_client()

    background_tasks = BackgroundTaskRunner()
    background_tasks.start_all(
        {
            "generation_job_relay": partial(
                run_generation_job_relay_worker,
                KafkaGenerationJobPublisher(producer),
            ),
            "consume_loop": partial(consume_loop, consumer),
        }
    )

    yield

    await background_tasks.shutdown()
    await app.state.ai_plot_client.aclose()
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
