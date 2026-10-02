import enum
from dataclasses import dataclass


class StepStatus(str, enum.Enum):
    OK = "ok"
    NEED_GENERATION = "need_generation"
    GENERATING = "generating"
    FINISHED = "finished"


@dataclass(frozen=True, slots=True)
class DialogueLine:
    """Реплика сцены"""

    id: int
    scene_id: int
    order: int
    text: str
    is_final_for_scene: bool
    background_asset_key: str | None
    sprite_asset_key: str | None
    outfit_asset_key: str | None
    emotion_asset_key: str | None


@dataclass(frozen=True, slots=True)
class Scene:
    """Сцена роадмапа"""

    id: int
    roadmap_id: int
    title: str
    order: int
    is_final_for_roadmap: bool
    is_final_for_novel: bool


@dataclass(frozen=True, slots=True)
class Character:
    """Персонаж, произносящий реплику"""

    id: int
    name: str
    role: str


@dataclass(frozen=True, slots=True)
class DialogueStep:
    """Реплика вместе со сценой и персонажем"""

    dialogue: DialogueLine
    scene: Scene
    character: Character


@dataclass(frozen=True, slots=True)
class NovelStep:
    """Ответ ai_plot на запрос следующей реплики.

    step заполнен при status=ok, next_scene_order — при need_generation/generating.
    """

    status: StepStatus
    step: DialogueStep | None = None
    next_scene_order: int | None = None
