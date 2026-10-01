from collections.abc import Awaitable, Callable

from src.inbound.kafka.handlers.generation_results import handle_generation_result

MessageHandler = Callable[[bytes], Awaitable[None]]

TOPIC_HANDLERS: dict[str, MessageHandler] = {
    "generation.results": handle_generation_result,
}
