from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.core.novels.exceptions import NovelNotFoundError, NovelGenerationError
from src.core.novels.services import NovelService
from src.inbound.http.novels.dependencies import get_novel_service
from src.inbound.http.novels.schemas import NovelCreateRequest, NovelResponse

router = APIRouter(prefix="/novels", tags=["novels"])


@router.post("/", response_model=NovelResponse)
async def create_novel(
    data: NovelCreateRequest,
    service: Annotated[NovelService, Depends(get_novel_service)],
):
    try:
        novel = await service.create_novel(data.prompt)
    except NovelGenerationError as e:
        raise HTTPException(status_code=502, detail="Failed to generate novel content")
    return novel


@router.get("/{novel_id}", response_model=NovelResponse)
async def get_novel(
    novel_id: int,
    service: Annotated[NovelService, Depends(get_novel_service)],
):
    try:
        return await service.get_novel(novel_id)
    except NovelNotFoundError:
        raise HTTPException(status_code=404, detail="Novel not found")


@router.get("/", response_model=list[NovelResponse])
async def list_novels(
    service: Annotated[NovelService, Depends(get_novel_service)],
):
    return await service.list_novels()


@router.delete("/{novel_id}", status_code=204)
async def delete_novel(
    novel_id: int,
    service: Annotated[NovelService, Depends(get_novel_service)],
):
    await service.delete_novel(novel_id)
