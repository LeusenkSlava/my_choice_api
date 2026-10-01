import uuid

from aiokafka import AIOKafkaProducer

from src.outbound.ai_plot.schemas import NovelCreateRequested
from src.outbound.ai_plot.topic import Topics


class AiPlotGateway:
    def __init__(self, producer: AIOKafkaProducer) -> None:
        self._producer = producer

    async def request_novel_generation(self, prompt: str, universe_id: int) -> None:
        command = NovelCreateRequested(
            request_id=str(uuid.uuid4()),
            prompt=prompt,
            universe_id=universe_id,
        )
        await self._producer.send_and_wait(
            Topics.NOVEL_EVENTS_CREATE, command.model_dump_json().encode()
        )
