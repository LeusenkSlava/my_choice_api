from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.core.generation_job.exceptions import GenerationJobNotFoundError
from src.core.generation_job.services.get_generation_job import (
    GetGenerationJobService,
)
from src.inbound.http.generation_jobs.dependencies import (
    get_get_generation_job_service,
)
from src.inbound.http.generation_jobs.schemas import GenerationJobStatusResponse

router = APIRouter(prefix="/generation-jobs", tags=["generation-jobs"])


@router.get("/{job_id}", response_model=GenerationJobStatusResponse)
async def get_generation_job(
    job_id: int,
    service: Annotated[
        GetGenerationJobService, Depends(get_get_generation_job_service)
    ],
):
    """Статус задачи генерации. Клиент опрашивает, пока status не станет done/failed."""
    try:
        job = await service.execute(job_id=job_id)
    except GenerationJobNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return GenerationJobStatusResponse.model_validate(job)
