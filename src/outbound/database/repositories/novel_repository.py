from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.novels.models import Novel
from src.outbound.database.models import NovelModel


class NovelRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, novel: Novel) -> Novel:
        db_novel = NovelModel(
            title=novel.title,
            description=novel.description,
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(db_novel)
        await self._session.flush()
        return self._to_domain(db_novel)

    async def get_by_id(self, novel_id: int) -> Novel | None:
        result = await self._session.execute(
            select(NovelModel).where(NovelModel.id == novel_id)
        )
        db_novel = result.scalar_one_or_none()
        return self._to_domain(db_novel) if db_novel else None

    async def list_all(self) -> list[Novel]:
        result = await self._session.execute(select(NovelModel))
        return [self._to_domain(n) for n in result.scalars().all()]

    async def delete(self, novel_id: int) -> None:
        db_novel = await self._session.get(NovelModel, novel_id)
        if db_novel:
            await self._session.delete(db_novel)

    @staticmethod
    def _to_domain(db_novel: NovelModel) -> Novel:
        return Novel(
            id=db_novel.id,
            title=db_novel.title,
            description=db_novel.description,
            created_at=db_novel.created_at,
            updated_at=db_novel.updated_at,
        )