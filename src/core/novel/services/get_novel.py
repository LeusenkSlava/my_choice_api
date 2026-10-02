from src.core.novel.interfaces import NovelProviderProtocol
from src.core.novel.models.novel import Novel


class GetNovelService:
    def __init__(self, provider: NovelProviderProtocol) -> None:
        self._provider = provider

    async def execute(self, novel_id: int) -> Novel:
        return await self._provider.get(novel_id)
