import asyncio
import logging
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)


class BackgroundTaskRunner:
    def __init__(self) -> None:
        self._tasks: list[asyncio.Task] = []

    def start_all(self, workers: dict[str, Callable[[], Awaitable[None]]]) -> None:
        for name, coro_factory in workers.items():
            self._tasks.append(asyncio.create_task(coro_factory(), name=name))

    async def shutdown(self) -> None:
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception(
                    "Background task %s failed during shutdown", task.get_name()
                )
