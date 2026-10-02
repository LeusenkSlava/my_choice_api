from typing import Protocol

from src.core.generation_job.models.generation_job import GenerationJob


class GenerationJobPublisherProtocol(Protocol):
    async def publish(
        self,
        job_id: int,
        user_prompt: str,
        universe_id: int,
    ) -> None: ...


class GenerationJobRepositoryProtocol(Protocol):
    async def get_active_by_dedup_key(
        self, dedup_key: str
    ) -> "GenerationJob | None": ...

    async def claim_created(self, limit: int) -> list["GenerationJob"]: ...
    async def release(self, job_id: int) -> None: ...
    async def mark_sent(self, job_id: int) -> None: ...
    async def mark_done(self, job_id: int, result_id: int) -> bool: ...
    async def mark_failed(self, job_id: int, error: str) -> bool: ...
