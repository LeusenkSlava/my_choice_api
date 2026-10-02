import logging

from pydantic import ValidationError

from src.core.generation_job.schemas.generation_result import GenerationResult
from src.core.generation_job.services.complete_generation_job import (
    CompleteGenerationJobService,
)
from src.outbound.database.dependencies import get_session_scope
from src.outbound.database.repositories.generation_job import GenerationJobRepository

logger = logging.getLogger(__name__)


async def handle_generation_result(raw: bytes) -> None:
    try:
        result = GenerationResult.model_validate_json(raw)
    except ValidationError as e:
        logger.warning("Невалидный GenerationResult, пропускаем: %s; raw=%r", e, raw[:1000])
        return

    async with get_session_scope() as session:
        generation_job_repository = GenerationJobRepository(session)
        service = CompleteGenerationJobService(generation_job_repository)
        await service.handle_result(result)
