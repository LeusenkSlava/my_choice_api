import json

from src.core.generation_job.interfaces import GenerationJobPublisherProtocol
from src.outbound.ai_plot.topic import Topics
from src.outbound.kafka.client import producer


class KafkaGenerationJobPublisher(GenerationJobPublisherProtocol):
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
        await producer.send_and_wait(Topics.NOVEL_EVENTS_CREATE, payload)
