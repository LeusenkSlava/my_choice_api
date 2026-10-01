from pydantic import BaseModel


class NovelCreateRequested(BaseModel):
    request_id: str
    prompt: str
    universe_id: int | None = None
