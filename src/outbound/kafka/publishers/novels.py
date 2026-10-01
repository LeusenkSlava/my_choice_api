import json
import uuid

from src.core.novels.interfaces import PlotGeneratorProtocol
from src.outbound.ai_plot.topic import Topics
from src.outbound.kafka.client import producer


class KafkaNovelEventPublisher(PlotGeneratorProtocol):
    async def publish_novel_created(self, user_prompt: str, universe_id: int) -> None:
        payload = json.dumps(
            {
                "request_id": str(uuid.uuid4()),
                "prompt": user_prompt,
                "universe_id": universe_id,
            }
        ).encode()
        await producer.send_and_wait(Topics.NOVEL_EVENTS_CREATE, payload)
