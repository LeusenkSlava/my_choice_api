import hashlib
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from src.core.generation_job.models.enums import JobStatus


class NovelCreateRequest(BaseModel):
    prompt: str
    universe_id: int | None = None

    @property
    def dedup_key(self) -> str:
        normalized_prompt = " ".join(self.prompt.split()).lower()
        raw = f"{normalized_prompt}:{self.universe_id}"
        return hashlib.sha256(raw.encode()).hexdigest()


class NovelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime

    title: str
    public_description: str
    description: str
    tone: str
    universe_id: int | None


class NovelListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[NovelResponse]
    total: int
    limit: int
    offset: int


class GenerationJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: JobStatus


class DialogueLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scene_id: int
    order: int
    text: str
    is_final_for_scene: bool
    background_asset_key: str | None
    sprite_asset_key: str | None
    outfit_asset_key: str | None
    emotion_asset_key: str | None


class SceneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    roadmap_id: int
    title: str
    order: int
    is_final_for_roadmap: bool
    is_final_for_novel: bool


class CharacterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    role: str


class DialogueStepResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dialogue: DialogueLineResponse
    scene: SceneResponse
    character: CharacterResponse


class NovelStepOkResponse(BaseModel):
    status: Literal["ok"] = "ok"
    step: DialogueStepResponse


class NovelStepGeneratingResponse(BaseModel):
    """Сцена генерируется: опрашивать GET /generation-jobs/{job.id}, затем повторить запрос."""

    status: Literal["generating"] = "generating"
    job: GenerationJobResponse


class NovelStepFinishedResponse(BaseModel):
    status: Literal["finished"] = "finished"
