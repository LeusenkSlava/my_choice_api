from dataclasses import dataclass
from datetime import datetime


@dataclass
class Novel:
    id: int | None
    created_at: datetime | None
    updated_at: datetime | None

    title: str
    public_description: str
    description: str
    tone: str
