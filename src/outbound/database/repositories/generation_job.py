from unittest import result

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.generation_job.exceptions import ActiveJobAlreadyExistsError
from src.core.generation_job.models.enums import JobKind, JobStatus
from src.core.generation_job.models.generation_job import GenerationJob
from src.outbound.database.errors import is_unique_violation
from src.outbound.database.models.generation_job import GenerationJobModel


class GenerationJobRepository:
    """Репозиторий задач на SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, generation_job: GenerationJob) -> GenerationJob:
        """Создать задачу на генерацию."""
        generation_job = GenerationJobModel(
            kind=generation_job.kind,
            payload=generation_job.payload,
            dedup_key=generation_job.dedup_key,
            status=generation_job.status,
            result_id=generation_job.result_id,
            error=generation_job.error,
        )
        try:
            async with self._session.begin_nested():
                self._session.add(generation_job)
        except IntegrityError as e:
            if is_unique_violation(e, "uq_active_job"):
                raise ActiveJobAlreadyExistsError from e
            raise
        return self._to_entity(generation_job)

    async def get_active_by_dedup_key(
        self,
        kind: JobKind,
        dedup_key: str,
    ) -> GenerationJob | None:
        """Получить активную задачу по ключу дедупликации."""
        stmt = select(GenerationJobModel).where(
            GenerationJobModel.kind == kind,
            GenerationJobModel.dedup_key == dedup_key,
            GenerationJobModel.status.in_(JobStatus.active()),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def claim_created(self, limit: int) -> list[GenerationJob]:
        """Захватить задачи со статусом CREATED."""
        subq = (
            select(GenerationJobModel.id)
            .where(GenerationJobModel.status == JobStatus.CREATED)
            .order_by(GenerationJobModel.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        stmt = (
            update(GenerationJobModel)
            .where(GenerationJobModel.id.in_(subq))
            .values(status=JobStatus.PUBLISHING)
            .returning(GenerationJobModel)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [self._to_entity(row) for row in rows]

    async def release(self, job_id: int) -> None:
        """Освободить задачу, вернув её в статус CREATED."""
        await self._session.execute(
            update(GenerationJobModel)
            .where(
                GenerationJobModel.id == job_id,
                GenerationJobModel.status == JobStatus.PUBLISHING,
            )
            .values(status=JobStatus.CREATED)
        )

    async def mark_sent(self, job_id: int) -> None:
        await self._session.execute(
            update(GenerationJobModel)
            .where(
                GenerationJobModel.id == job_id,
                GenerationJobModel.status == JobStatus.PUBLISHING,
            )
            .values(status=JobStatus.SENT)
        )

    async def mark_done(self, job_id: int, result_id: int) -> bool:
        result = await self.session.execute(
            update(GenerationJobModel)
            .where(
                GenerationJobModel.id == job_id,
                GenerationJobModel.status.in_(JobStatus.active()),
            )
            .values(status=JobStatus.DONE, result_id=result_id)
        )
        return result.rowcount > 0

    async def mark_failed(self, job_id: int, error: str | None) -> None:
        result = await self._session.execute(
            update(GenerationJobModel)
            .where(
                GenerationJobModel.id == job_id,
                GenerationJobModel.status.in_(JobStatus.active()),
            )
            .values(status=JobStatus.FAILED, error=error)
        )
        return result.rowcount > 0

    @staticmethod
    def _to_entity(model: GenerationJobModel) -> GenerationJob:
        return GenerationJob(
            id=model.id,
            kind=model.kind,
            payload=model.payload,
            dedup_key=model.dedup_key,
            status=model.status,
            result_id=model.result_id,
            error=model.error,
        )
