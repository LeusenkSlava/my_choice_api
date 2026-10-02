from collections.abc import Awaitable, Callable

from src.inbound.kafka.handlers.generation_results import handle_generation_result
from src.outbound.ai_plot.topic import Topics

MessageHandler = Callable[[bytes], Awaitable[None]]

TOPIC_HANDLERS: dict[str, MessageHandler] = {
    Topics.GENERATION_RESULTS: handle_generation_result,
}
