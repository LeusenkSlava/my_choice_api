import httpx
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.generation_job.services.create_generation_job import (
    CreateGenerationJobService,
)
from src.core.novel.services.delete_novel import DeleteNovelService
from src.core.novel.services.get_novel import GetNovelService
from src.core.novel.services.list_novels import ListNovelsService
from src.core.novel.services.read_novel import ReadNovelService
from src.outbound.ai_plot.novel_provider import AiPlotNovelProvider
from src.outbound.database.dependencies import get_db_session
from src.outbound.database.repositories.generation_job import GenerationJobRepository


def get_generation_job_repo(
    session: AsyncSession = Depends(get_db_session),
) -> GenerationJobRepository:
    return GenerationJobRepository(session=session)


def get_create_generation_job_service(
    repo: GenerationJobRepository = Depends(get_generation_job_repo),
) -> CreateGenerationJobService:
    return CreateGenerationJobService(generation_job_repo=repo)


def get_ai_plot_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.ai_plot_client


def get_novel_provider(
    client: httpx.AsyncClient = Depends(get_ai_plot_client),
) -> AiPlotNovelProvider:
    return AiPlotNovelProvider(client=client)


def get_get_novel_service(
    provider: AiPlotNovelProvider = Depends(get_novel_provider),
) -> GetNovelService:
    return GetNovelService(provider=provider)


def get_list_novels_service(
    provider: AiPlotNovelProvider = Depends(get_novel_provider),
) -> ListNovelsService:
    return ListNovelsService(provider=provider)


def get_delete_novel_service(
    provider: AiPlotNovelProvider = Depends(get_novel_provider),
) -> DeleteNovelService:
    return DeleteNovelService(provider=provider)


def get_read_novel_service(
    provider: AiPlotNovelProvider = Depends(get_novel_provider),
    create_job_service: CreateGenerationJobService = Depends(
        get_create_generation_job_service
    ),
) -> ReadNovelService:
    return ReadNovelService(provider=provider, create_job_service=create_job_service)
