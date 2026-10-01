import asyncio
import logging

from src.core.generation_job.services.publish_generation_job import (
    PublishGenerationJobsService,
)
from src.outbound.database.dependencies import get_session_scope
from src.outbound.database.repositories.generation_job import GenerationJobRepository
from src.outbound.kafka.publishers.generation_job import KafkaGenerationJobPublisher

logger = logging.getLogger(__name__)


async def run_generation_job_relay_worker(interval: float = 1.0) -> None:
    """Фоновая задача для публикации задач на генерацию в Kafka."""

    while True:
        try:
            async with get_session_scope() as session:
                repository = GenerationJobRepository(session)
                publisher = PublishGenerationJobsService(
                    repository=repository,
                    publisher=KafkaGenerationJobPublisher(),
                )
                await publisher.publish_batch()
        except Exception as e:
            logger.error(f"Error occurred while publishing generation jobs: {e}")

        await asyncio.sleep(interval)
