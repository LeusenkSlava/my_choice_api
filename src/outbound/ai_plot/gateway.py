import uuid

from src.outbound.ai_plot.schemas import NovelCreateRequested
from src.outbound.ai_plot.topic import Topics
from src.outbound.kafka.client import producer


class AiPlotGateway:
    async def request_novel_generation(self, prompt: str, universe_id: int) -> None:
        command = NovelCreateRequested(
            request_id=str(uuid.uuid4()),
            prompt=prompt,
            universe_id=universe_id,
        )
        await producer.send_and_wait(
            Topics.NOVEL_EVENTS_CREATE, command.model_dump_json().encode()
        )
