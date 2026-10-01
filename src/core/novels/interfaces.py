from typing import Protocol


class PlotGeneratorProtocol(Protocol):
    async def request_novel_generation(self, prompt: str, universe_id: int) -> None: ...
