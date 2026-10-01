import uuid
from dataclasses import dataclass
from datetime import datetime

from src.core.generation_job.models.enums import JobKind, JobStatus


@dataclass(frozen=True, slots=True)
class GenerationJob:
    """Задача на генерацию"""

    kind: JobKind
    payload: dict
    dedup_key: str
    status: JobStatus = None
    result_id: uuid.UUID | None = None
    error: str | None = None
    id: int = None
    created_at: datetime = None
    updated_at: datetime = None
