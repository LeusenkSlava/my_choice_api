from datetime import datetime

from pydantic import BaseModel

from src.core.novel.models.novel import Novel
from src.core.novel.models.step import (
    Character,
    DialogueLine,
    DialogueStep,
    NovelStep,
    Scene,
    StepStatus,
)


class NovelCreateRequested(BaseModel):
    request_id: str
    prompt: str
    universe_id: int | None = None


class AiPlotNovel(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    title: str
    public_description: str
    description: str
    tone: str
    universe_id: int | None = None

    def to_domain(self) -> Novel:
        return Novel(**self.model_dump())


class AiPlotNovelList(BaseModel):
    items: list[AiPlotNovel]
    total: int
    limit: int
    offset: int


class AiPlotDialogueLine(BaseModel):
    id: int
    scene_id: int
    order: int
    text: str
    is_final_for_scene: bool
    background_asset_key: str | None
    sprite_asset_key: str | None
    outfit_asset_key: str | None
    emotion_asset_key: str | None


class AiPlotScene(BaseModel):
    id: int
    roadmap_id: int
    title: str
    order: int
    is_final_for_roadmap: bool
    is_final_for_novel: bool


class AiPlotCharacter(BaseModel):
    id: int
    name: str
    role: str


class AiPlotDialogueStep(BaseModel):
    dialogue: AiPlotDialogueLine
    scene: AiPlotScene
    character: AiPlotCharacter


class AiPlotNovelStep(BaseModel):
    status: StepStatus
    step: AiPlotDialogueStep | None = None
    next_scene_order: int | None = None

    def to_domain(self) -> NovelStep:
        step = None
        if self.step is not None:
            step = DialogueStep(
                dialogue=DialogueLine(**self.step.dialogue.model_dump()),
                scene=Scene(**self.step.scene.model_dump()),
                character=Character(**self.step.character.model_dump()),
            )
        return NovelStep(
            status=self.status, step=step, next_scene_order=self.next_scene_order
        )


class SceneGenerateRequested(BaseModel):
    job_id: int
    novel_id: int
    scene_order: int
