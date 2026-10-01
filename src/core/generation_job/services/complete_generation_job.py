import logging

from src.core.generation_job.interfaces import GenerationJobRepositoryProtocol
from src.core.generation_job.schemas.generation_result import GenerationResult

logger = logging.getLogger(__name__)


class CompleteGenerationJobService:
    def __init__(
        self,
        repository: GenerationJobRepositoryProtocol,
    ):
        self._repository = repository

    async def handle_result(self, result: GenerationResult) -> None:
        if result.status == "done":
            updated = await self.repository.mark_done(result.job_id, result.result_id)
        else:
            updated = await self.repository.mark_failed(result.job_id, result.error)

        if not updated:
            logger.info(
                "Job %s уже завершена или не найдена, пропускаем", result.job_id
            )
