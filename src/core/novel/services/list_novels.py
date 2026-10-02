from src.core.novel.interfaces import NovelProviderProtocol
from src.core.novel.models.novel import NovelPage


class ListNovelsService:
    def __init__(self, provider: NovelProviderProtocol) -> None:
        self._provider = provider

    async def execute(self, limit: int, offset: int) -> NovelPage:
        return await self._provider.list(limit=limit, offset=offset)
