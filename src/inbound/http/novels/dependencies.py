from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.novels.services import NovelService
from src.outbound.ai.deepseek_client import DeepSeekNovelGenerator
from src.outbound.ai.dependencies import get_deepseek_generator
from src.outbound.database.dependencies import get_db_session
from src.outbound.database.repositories.novel_repository import NovelRepository


def get_novel_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> NovelRepository:
    return NovelRepository(session)


def get_novel_service(
    repository: Annotated[NovelRepository, Depends(get_novel_repository)],
    generator: Annotated[DeepSeekNovelGenerator, Depends(get_deepseek_generator)],
) -> NovelService:
    return NovelService(repository, generator)