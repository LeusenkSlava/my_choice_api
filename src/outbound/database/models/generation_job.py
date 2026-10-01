import uuid

from sqlalchemy import Index, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.generation_job.models.enums import JobKind, JobStatus
from src.outbound.database.models.base_model import BaseModel
from src.outbound.database.utils import pg_enum

_ACTIVE_STATUSES_SQL = ", ".join(f"'{s.value}'" for s in JobStatus.active())


class GenerationJobModel(BaseModel):
    __tablename__ = "generation_jobs"
    __table_args__ = (
        Index(
            "uq_active_job",
            "kind",
            "dedup_key",
            unique=True,
            postgresql_where=text(f"status IN ({_ACTIVE_STATUSES_SQL})"),
        ),
        Index(
            "ix_jobs_created",
            "created_at",
            postgresql_where=text("status = 'created'"),
        ),
    )

    kind: Mapped[JobKind] = mapped_column(
        pg_enum(JobKind, native=False), nullable=False
    )
    payload: Mapped[dict] = mapped_column(JSONB)
    dedup_key: Mapped[str] = mapped_column(String(128))
    status: Mapped[JobStatus] = mapped_column(
        pg_enum(JobStatus, native=True),
        nullable=False,
        server_default=JobStatus.CREATED.value,
    )
    result_id: Mapped[uuid.UUID | None]
    error: Mapped[str | None]
