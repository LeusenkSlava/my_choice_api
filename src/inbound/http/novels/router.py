import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.core.generation_job.exceptions import NovelGenerationError
from src.core.generation_job.services.create_generation_job import (
    CreateGenerationJobService,
)
from src.inbound.http.novels.dependencies import get_create_generation_job_service
from src.inbound.http.novels.schemas import GenerationJobResponse, NovelCreateRequest

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/novels", tags=["novels"])


@router.post("/", status_code=202, response_model=GenerationJobResponse)
async def create_novel(
    data: NovelCreateRequest,
    service: Annotated[
        CreateGenerationJobService, Depends(get_create_generation_job_service)
    ],
):
    try:
        generation_job = await service.execute(data=data)
    except NovelGenerationError as e:
        logger.error(
            f"Failed to generate novel content for prompt '{data.prompt}': {e}"
        )
        raise HTTPException(status_code=502, detail="Failed to generate novel content")

    return GenerationJobResponse.model_validate(generation_job)
