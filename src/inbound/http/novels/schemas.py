from datetime import datetime

from pydantic import BaseModel


class NovelCreateRequest(BaseModel):
    prompt: str
    universe_id: int


class NovelResponse(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime

    title: str
    public_description: str
    tone: str
