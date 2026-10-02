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

    async def execute(
        self, kind: JobKind, payload: dict, dedup_key: str
    ) -> GenerationJob:
        """Создать задачу или вернуть уже активную с тем же dedup_key."""
        existing = await self._generation_job_repo.get_active_by_dedup_key(
            kind=kind, dedup_key=dedup_key
        )
        if existing is not None:
            return existing

        generation_job = GenerationJob(
            payload=payload,
            dedup_key=dedup_key,
            kind=kind,
        )
        try:
            created = await self._generation_job_repo.create(generation_job)
        except ActiveJobAlreadyExistsError:
            existing = await self._generation_job_repo.get_active_by_dedup_key(
                kind=kind, dedup_key=dedup_key
            )
            return existing

        return created
