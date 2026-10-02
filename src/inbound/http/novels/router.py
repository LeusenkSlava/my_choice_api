import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from src.core.generation_job.exceptions import NovelGenerationError
from src.core.generation_job.models.enums import JobKind
from src.core.generation_job.services.create_generation_job import (
    CreateGenerationJobService,
)
from src.core.novel.exceptions import NovelNotFoundError, NovelProviderUnavailableError
from src.core.novel.services.delete_novel import DeleteNovelService
from src.core.novel.services.get_novel import GetNovelService
from src.core.novel.models.step import StepStatus
from src.core.novel.services.list_novels import ListNovelsService
from src.core.novel.services.read_novel import ReadNovelService
from src.inbound.http.novels.dependencies import (
    get_create_generation_job_service,
    get_delete_novel_service,
    get_get_novel_service,
    get_list_novels_service,
    get_read_novel_service,
)
from src.inbound.http.novels.schemas import (
    GenerationJobResponse,
    DialogueStepResponse,
    NovelCreateRequest,
    NovelListResponse,
    NovelResponse,
    NovelStepFinishedResponse,
    NovelStepGeneratingResponse,
    NovelStepOkResponse,
)

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
        generation_job = await service.execute(
            kind=JobKind.NOVEL,
            payload=data.model_dump(mode="json"),
            dedup_key=data.dedup_key,
        )
    except NovelGenerationError as e:
        logger.error(
            f"Failed to generate novel content for prompt '{data.prompt}': {e}"
        )
        raise HTTPException(status_code=502, detail="Failed to generate novel content")

    return GenerationJobResponse.model_validate(generation_job)


@router.get("/", response_model=NovelListResponse)
async def list_novels(
    service: Annotated[ListNovelsService, Depends(get_list_novels_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    try:
        page = await service.execute(limit=limit, offset=offset)
    except NovelProviderUnavailableError as e:
        logger.error(f"Failed to list novels: {e}")
        raise HTTPException(status_code=502, detail="Novel provider unavailable")

    return NovelListResponse.model_validate(page)


@router.get("/{novel_id}", response_model=NovelResponse)
async def get_novel(
    novel_id: int,
    service: Annotated[GetNovelService, Depends(get_get_novel_service)],
):
    try:
        novel = await service.execute(novel_id=novel_id)
    except NovelNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NovelProviderUnavailableError as e:
        logger.error(f"Failed to get novel {novel_id}: {e}")
        raise HTTPException(status_code=502, detail="Novel provider unavailable")

    return NovelResponse.model_validate(novel)


@router.get(
    "/{novel_id}/next",
    response_model=NovelStepOkResponse
    | NovelStepGeneratingResponse
    | NovelStepFinishedResponse,
    responses={202: {"model": NovelStepGeneratingResponse}},
)
async def read_next(
    novel_id: int,
    response: Response,
    service: Annotated[ReadNovelService, Depends(get_read_novel_service)],
    offset: Annotated[int | None, Query()] = None,
):
    """Следующая реплика новеллы.

    offset — id последней показанной реплики; без него новелла начинается с начала.
    200 ok — реплика; 200 finished — новелла пройдена;
    202 generating — сцена генерируется, опрашивать GET /generation-jobs/{job.id},
    после status=done повторить запрос с тем же offset.
    """
    try:
        result = await service.execute(novel_id=novel_id, offset=offset)
    except NovelNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NovelProviderUnavailableError as e:
        logger.error(f"Failed to read novel {novel_id} at offset {offset}: {e}")
        raise HTTPException(status_code=502, detail="Novel provider unavailable")

    if result.status == StepStatus.FINISHED:
        return NovelStepFinishedResponse()
    if result.status == StepStatus.GENERATING:
        response.status_code = 202
        return NovelStepGeneratingResponse(
            job=GenerationJobResponse.model_validate(result.job)
        )
    return NovelStepOkResponse(step=DialogueStepResponse.model_validate(result.step))


@router.delete("/{novel_id}", status_code=204)
async def delete_novel(
    novel_id: int,
    service: Annotated[DeleteNovelService, Depends(get_delete_novel_service)],
):
    try:
        await service.execute(novel_id=novel_id)
    except NovelNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NovelProviderUnavailableError as e:
        logger.error(f"Failed to delete novel {novel_id}: {e}")
        raise HTTPException(status_code=502, detail="Novel provider unavailable")

    return Response(status_code=204)
