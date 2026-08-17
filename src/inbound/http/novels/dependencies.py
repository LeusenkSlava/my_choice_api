from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.novels.services.novel import NovelService, CharacterService, RoadmapService, DialogueActionService, DialogueLineService
from src.core.novels.services.novel_generator import NovelGeneratorService
from src.outbound.ai.deepseek_client import DeepSeekNovelGenerator
from src.outbound.ai.dependencies import get_deepseek_generator
from src.outbound.database.dependencies import get_db_session
from src.outbound.database.repositories.novel_repository import NovelRepository, CharacterRepository, RoadmapRepository, DialogueActionRepository, DialogueLineRepository


def get_novel_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> NovelRepository:
    return NovelRepository(session)

def get_character_repository(
        session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CharacterRepository:
    return CharacterRepository(session)

def get_roadmap_repository(
        session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RoadmapRepository:
    return RoadmapRepository(session)

def get_dialogue_action_repository(
        session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DialogueActionRepository:
    return DialogueActionRepository(session)

def get_dialogue_line_repository(
        session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DialogueLineRepository:
    return DialogueLineRepository(session)

def get_novel_service(
        repository: Annotated[NovelRepository, Depends(get_novel_repository)],
) -> NovelService:
    return NovelService(repository)

def get_novel_generator_service(
    novel_repository: Annotated[NovelRepository, Depends(get_novel_repository)],
    charecter_repository: Annotated[CharacterRepository, Depends(get_character_repository)],
    roadmap_repsitory: Annotated[RoadmapRepository, Depends(get_roadmap_repository)],
    generator: Annotated[DeepSeekNovelGenerator, Depends(get_deepseek_generator)],
    dialogue_line_repository: Annotated[DialogueLineRepository, Depends(get_dialogue_line_repository)],
    dialogue_action_repository: Annotated[DialogueActionRepository, Depends(get_dialogue_action_repository)],
) -> NovelGeneratorService:
    novel_service = NovelService(novel_repository)
    character_service = CharacterService(charecter_repository)
    roadmap_service = RoadmapService(roadmap_repsitory)
    dialogue_action_service = DialogueActionService(dialogue_action_repository)
    dialogue_line_service = DialogueLineService(dialogue_line_repository)
    return NovelGeneratorService(
        novel_service=novel_service,
        character_service=character_service,
        roadmap_service=roadmap_service,
        generator=generator,
        dialogue_action_service=dialogue_action_service,
        dialogue_line_service=dialogue_line_service,
    )