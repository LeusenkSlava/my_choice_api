from typing import Literal

from pydantic import BaseModel, model_validator


class GenerationResult(BaseModel):
    job_id: int
    status: Literal["done", "failed"]
    result_id: int | None = None
    error: str | None = None

    @model_validator(mode="after")
    def check_consistency(self) -> "GenerationResult":
        if self.status == "done" and self.result_id is None:
            raise ValueError("result_id required for status='done'")
        return self
