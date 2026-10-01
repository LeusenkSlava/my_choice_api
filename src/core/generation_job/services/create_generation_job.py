from src.core.generation_job.exceptions import ActiveJobAlreadyExistsError
from src.core.generation_job.interfaces import GenerationJobRepositoryProtocol
from src.core.generation_job.models.enums import JobKind
from src.core.generation_job.models.generation_job import GenerationJob


class CreateGenerationJobService:

    def __init__(
        self,
        generation_job_repo: GenerationJobRepositoryProtocol,
    ):
        self._generation_job_repo = generation_job_repo

    async def execute(self, data) -> GenerationJob:
        existing = await self._generation_job_repo.get_active_by_dedup_key(
            kind=JobKind.NOVEL, dedup_key=data.dedup_key
        )
        if existing is not None:
            return existing

        generation_job = GenerationJob(
            payload=data.model_dump(mode="json"),
            dedup_key=data.dedup_key,
            kind=JobKind.NOVEL,
        )
        try:
            created = await self._generation_job_repo.create(generation_job)
        except ActiveJobAlreadyExistsError:
            existing = await self._generation_job_repo.get_active_by_dedup_key(
                kind=JobKind.NOVEL, dedup_key=data.dedup_key
            )
            return existing

        return created
