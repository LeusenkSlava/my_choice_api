import logging

from src.core.generation_job.interfaces import (
    GenerationJobPublisherProtocol,
    GenerationJobRepositoryProtocol,
)

logger = logging.getLogger(__name__)


class PublishGenerationJobsService:
    def __init__(
        self,
        repository: GenerationJobRepositoryProtocol,
        publisher: GenerationJobPublisherProtocol,
    ) -> None:
        self._repository = repository
        self._publisher = publisher

    async def publish_batch(self) -> None:
        """Проверить наличие активной задачи и при необходимости отправить"""
        jobs = await self._repository.claim_created(limit=10)
        for job in jobs:
            try:
                await self._publisher.publish(
                    id=job.id,
                    user_prompt=job.payload["prompt"],
                    universe_id=job.payload["universe_id"],
                )
            except Exception as e:
                logger.error(f"Failed to publish job {job.id}: {e}")
                await self._repository.release(job_id=job.id)
                continue

            await self._repository.mark_sent(job.id)
