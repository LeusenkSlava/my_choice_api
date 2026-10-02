import logging
from dataclasses import dataclass

from src.core.generation_job.models.enums import JobKind
from src.core.generation_job.models.generation_job import GenerationJob
from src.core.generation_job.services.create_generation_job import (
    CreateGenerationJobService,
)
from src.core.novel.exceptions import NovelProviderUnavailableError
from src.core.novel.interfaces import NovelProviderProtocol
from src.core.novel.models.step import DialogueStep, StepStatus

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ReadNovelResult:
    """Результат чтения: реплика (ok), задача генерации (generating) или конец (finished)."""

    status: StepStatus
    step: DialogueStep | None = None
    job: GenerationJob | None = None


class ReadNovelService:
    def __init__(
        self,
        provider: NovelProviderProtocol,
        create_job_service: CreateGenerationJobService,
    ) -> None:
        self._provider = provider
        self._create_job_service = create_job_service

    async def execute(self, novel_id: int, offset: int | None) -> ReadNovelResult:
        result = await self._provider.get_step(novel_id, offset)

        if result.status == StepStatus.FINISHED:
            return ReadNovelResult(status=StepStatus.FINISHED)

        if result.status in (StepStatus.NEED_GENERATION, StepStatus.GENERATING):
            job = await self._request_scene(novel_id, result.next_scene_order)
            return ReadNovelResult(status=StepStatus.GENERATING, job=job)

        step = result.step
        if step.dialogue.is_final_for_scene and not step.scene.is_final_for_novel:
            await self._prefetch_next_scene(novel_id, step.dialogue.id)

        return ReadNovelResult(status=StepStatus.OK, step=step)

    async def _prefetch_next_scene(self, novel_id: int, last_dialogue_id: int) -> None:
        """Пока пользователь читает последнюю реплику сцены — запускаем генерацию следующей."""
        try:
            ahead = await self._provider.get_step(novel_id, last_dialogue_id)
        except NovelProviderUnavailableError as e:
            logger.warning("Prefetch сцены для новеллы %s не удался: %s", novel_id, e)
            return

        if ahead.status in (StepStatus.NEED_GENERATION, StepStatus.GENERATING):
            await self._request_scene(novel_id, ahead.next_scene_order)

    async def _request_scene(self, novel_id: int, scene_order: int) -> GenerationJob:
        return await self._create_job_service.execute(
            kind=JobKind.SCENE,
            payload={"novel_id": novel_id, "scene_order": scene_order},
            dedup_key=f"{novel_id}:{scene_order}",
        )
