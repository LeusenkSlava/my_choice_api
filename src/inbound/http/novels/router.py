import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.core.novels.exceptions import NovelGenerationError
from src.core.novels.services.crud import NovelCRUDService
from src.inbound.http.novels.dependencies import get_novel_crud_service
from src.inbound.http.novels.schemas import NovelCreateRequest

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/novels", tags=["novels"])


@router.post("/", status_code=204)
async def create_novel(
    data: NovelCreateRequest,
    service: Annotated[NovelCRUDService, Depends(get_novel_crud_service)],
):
    try:
        await service.create(prompt=data.prompt, universe_id=data.universe_id)
    except NovelGenerationError as e:
        logger.error(
            f"Failed to generate novel content for prompt '{data.prompt}': {e}"
        )
        raise HTTPException(status_code=502, detail="Failed to generate novel content")
