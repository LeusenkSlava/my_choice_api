from pydantic import BaseModel, ConfigDict

from src.core.generation_job.models.enums import JobKind, JobStatus


class GenerationJobStatusResponse(BaseModel):
    """result_id — id новеллы (kind=novel) или сцены (kind=scene), заполняется при status=done."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: JobKind
    status: JobStatus
    result_id: int | None
    error: str | None
