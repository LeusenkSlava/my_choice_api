from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Novel:
    """Сгенерированная новелла"""

    id: int
    created_at: datetime
    updated_at: datetime
    title: str
    public_description: str
    description: str
    tone: str
    universe_id: int | None


@dataclass(frozen=True, slots=True)
class NovelPage:
    """Страница списка новелл"""

    items: list[Novel]
    total: int
    limit: int
    offset: int
