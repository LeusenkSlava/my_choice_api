from src.core.novel.interfaces import NovelProviderProtocol


class DeleteNovelService:
    def __init__(self, provider: NovelProviderProtocol) -> None:
        self._provider = provider

    async def execute(self, novel_id: int) -> None:
        await self._provider.delete(novel_id)
