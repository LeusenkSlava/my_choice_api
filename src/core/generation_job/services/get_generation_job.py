from src.core.generation_job.exceptions import GenerationJobNotFoundError
from src.core.generation_job.interfaces import GenerationJobRepositoryProtocol
from src.core.generation_job.models.generation_job import GenerationJob


class GetGenerationJobService:
    def __init__(self, repository: GenerationJobRepositoryProtocol) -> None:
        self._repository = repository

    async def execute(self, job_id: int) -> GenerationJob:
        job = await self._repository.get_by_id(job_id)
        if job is None:
            raise GenerationJobNotFoundError(job_id)
        return job
