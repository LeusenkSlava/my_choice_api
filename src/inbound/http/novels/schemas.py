import hashlib
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.core.generation_job.models.enums import JobStatus


class NovelCreateRequest(BaseModel):
    prompt: str
    universe_id: int

    @property
    def dedup_key(self) -> str:
        normalized_prompt = " ".join(self.prompt.split()).lower()
        raw = f"{normalized_prompt}:{self.universe_id}"
        return hashlib.sha256(raw.encode()).hexdigest()


class NovelResponse(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime

    title: str
    public_description: str
    tone: str


class GenerationJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: JobStatus
