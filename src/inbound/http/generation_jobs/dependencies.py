from fastapi import Depends

from src.core.generation_job.services.get_generation_job import (
    GetGenerationJobService,
)
from src.inbound.http.novels.dependencies import get_generation_job_repo
from src.outbound.database.repositories.generation_job import GenerationJobRepository


def get_get_generation_job_service(
    repo: GenerationJobRepository = Depends(get_generation_job_repo),
) -> GetGenerationJobService:
    return GetGenerationJobService(repository=repo)
