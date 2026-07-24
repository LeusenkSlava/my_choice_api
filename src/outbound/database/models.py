from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, declarative_base, relationship

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id})>"


class CharacterModel(BaseModel):
    __tablename__ = "characters"

    novel_id: Mapped[int] = mapped_column(Integer, ForeignKey("novels.id"), nullable=False)
    name: Mapped[str]
    role: Mapped[str]
    arc: Mapped[str]
    voice_notes: Mapped[str]

    # Relationship back to novel (optional but useful)
    novel: Mapped["NovelModel"] = relationship("NovelModel", back_populates="characters")

    def __repr__(self):
        return f"<CharacterModel(id={self.id}, name={self.name}, novel_id={self.novel_id})>"


class RoadmapModel(BaseModel):
    __tablename__ = "roadmap"

    novel_id: Mapped[int] = mapped_column(Integer, ForeignKey("novels.id"), nullable=False)
    step_id: Mapped[int]
    title: Mapped[str]
    goal: Mapped[str]
    target_choice: Mapped[bool]
    choice_stakes: Mapped[Optional[str]]

    novel: Mapped["NovelModel"] = relationship("NovelModel", back_populates="roadmap")

    def __repr__(self):
        return f"<RoadmapModel(id={self.id}, step_id={self.step_id}, novel_id={self.novel_id})>"


class NovelModel(BaseModel):
    __tablename__ = "novels"

    title: Mapped[str]
    public_description: Mapped[str]
    tone: Mapped[str]

    characters: Mapped[List["CharacterModel"]] = relationship(
        "CharacterModel",
        back_populates="novel",
        cascade="all, delete-orphan"
    )
    roadmap: Mapped[List["RoadmapModel"]] = relationship(
        "RoadmapModel",
        back_populates="novel",
        cascade="all, delete-orphan",
        order_by="RoadmapModel.step_id"
    )
