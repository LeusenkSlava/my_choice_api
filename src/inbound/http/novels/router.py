import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.core.novels.exceptions import NovelNotFoundError, NovelGenerationError
from src.core.novels.services.novel import NovelService
from src.core.novels.services.novel_generator import NovelGeneratorService
from src.inbound.http.novels.dependencies import get_novel_service, get_novel_generator_service
from src.inbound.http.novels.schemas import NovelCreateRequest, NovelResponse

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/novels", tags=["novels"])


@router.post("/", response_model=NovelResponse)
async def create_novel(
    data: NovelCreateRequest,
    service: Annotated[NovelGeneratorService, Depends(get_novel_generator_service)],
):
    try:
        novel = await service.generator(data.prompt)
    except NovelGenerationError as e:
        logger.error(e)
        raise HTTPException(status_code=502, detail="Failed to generate novel content")
    return novel


@router.get("/{novel_id}", response_model=NovelResponse)
async def get_novel(
    novel_id: int,
    service: Annotated[NovelService, Depends(get_novel_service)],
):
    novel = await service.get(novel_id)
    if novel is None:
        raise HTTPException(status_code=404, detail="Novel not found")
    return novel



@router.get("/", response_model=list[NovelResponse])
async def list_novels(
    service: Annotated[NovelService, Depends(get_novel_service)],
):
    return await service.list()


@router.delete("/{novel_id}", status_code=204)
async def delete_novel(
    novel_id: int,
    service: Annotated[NovelService, Depends(get_novel_service)],
):
    await service.delete(novel_id)


@router.get("/{novel_id}/{roadmap_id}", status_code=204)
async def start_novel(
    novel_id: int,
    roadmap_id: int,
    service: Annotated[NovelGeneratorService, Depends(get_novel_generator_service)],
):
    await service.start(novel_id=novel_id, roadmap_id=roadmap_id)

