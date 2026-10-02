import json

from aiokafka import AIOKafkaProducer

from src.core.generation_job.interfaces import GenerationJobPublisherProtocol
from src.core.generation_job.models.enums import JobKind
from src.core.generation_job.models.generation_job import GenerationJob
from src.outbound.ai_plot.schemas import SceneGenerateRequested
from src.outbound.ai_plot.topic import Topics


class KafkaGenerationJobPublisher(GenerationJobPublisherProtocol):
    def __init__(self, producer: AIOKafkaProducer) -> None:
        self._producer = producer

    async def publish(self, job: GenerationJob) -> None:
        if job.kind == JobKind.NOVEL:
            await self._publish_novel(job)
        elif job.kind == JobKind.SCENE:
            await self._publish_scene(job)
        else:
            raise ValueError(f"Неизвестный тип задачи: {job.kind}")

    async def _publish_novel(self, job: GenerationJob) -> None:
        payload = json.dumps(
            {
                "job_id": job.id,
                "prompt": job.payload["prompt"],
                "universe_id": job.payload["universe_id"],
            }
        ).encode()
        await self._producer.send_and_wait(Topics.NOVEL_EVENTS_CREATE, payload)

    async def _publish_scene(self, job: GenerationJob) -> None:
        command = SceneGenerateRequested(
            job_id=job.id,
            novel_id=job.payload["novel_id"],
            scene_order=job.payload["scene_order"],
        )
        # ключ = novel_id: все сцены одной новеллы попадают в одну партицию по порядку
        await self._producer.send_and_wait(
            Topics.SCENE_GENERATE,
            command.model_dump_json().encode(),
            key=str(command.novel_id).encode(),
        )
