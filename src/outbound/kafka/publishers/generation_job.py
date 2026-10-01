import json

from src.core.generation_job.interfaces import GenerationJobPublisherProtocol
from src.outbound.ai_plot.topic import Topics
from aiokafka import AIOKafkaProducer



class KafkaGenerationJobPublisher(GenerationJobPublisherProtocol):
    def __init__(self, producer: AIOKafkaProducer) -> None:
        self._producer = producer

    async def publish(
        self,
        id: int,
        user_prompt: str,
        universe_id: int,
    ) -> None:
        payload = json.dumps(
            {
                "request_id": str(id),
                "prompt": user_prompt,
                "universe_id": universe_id,
            }
        ).encode()
        await self._producer.send_and_wait(Topics.NOVEL_EVENTS_CREATE, payload)
