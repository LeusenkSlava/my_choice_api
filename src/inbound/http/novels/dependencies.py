from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.generation_job.services.create_generation_job import (
    CreateGenerationJobService,
)
from src.outbound.database.dependencies import get_db_session
from src.outbound.database.repositories.generation_job import GenerationJobRepository


def get_generation_job_repo(
    session: AsyncSession = Depends(get_db_session),
) -> GenerationJobRepository:
    return GenerationJobRepository(session=session)


def get_create_generation_job_service(
    repo: GenerationJobRepository = Depends(get_generation_job_repo),
) -> CreateGenerationJobService:
    return CreateGenerationJobService(generation_job_repo=repo)
