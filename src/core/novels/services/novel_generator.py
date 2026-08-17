import logging

from src.core.novels.exceptions import NovelGenerationError
from src.core.novels.interfaces import NovelGeneratorProtocol
from src.core.novels.models import Novel, Character, Roadmap, DialogueAction, DialogueLine
from src.core.novels.services.novel import NovelService, RoadmapService, CharacterService, DialogueActionService, \
    DialogueLineService

logger = logging.getLogger(__name__)


class NovelGeneratorService:
    def __init__(
        self,
        novel_service: NovelService,
        roadmap_service: RoadmapService,
        character_service: CharacterService,
        dialogue_line_service: DialogueLineService,
        dialogue_action_service: DialogueActionService,
        generator: NovelGeneratorProtocol,
    ):
        self._novel_service = novel_service
        self._roadmap_service = roadmap_service
        self._character_service = character_service
        self._dialogue_line_service = dialogue_line_service
        self._dialogue_action_service = dialogue_action_service
        self._generator = generator

    async def __create_promt(self, prompt: str) -> list:
        system_promt = {
            "role": "system",
            "content": (
                "Ты сценарист интерактивных визуальных новелл."
                "По тегам и описанию от пользователя создай творческую основу истории для дальнейшей генерации."
                "Создай:"
                "1. Название — короткое, цепляющее."
                "2. Описание для пользователя — 1-2 предложения, БЕЗ спойлеров."
                "3. Персонажи — имя, роль, внутренняя арка, особенности характера/речи."
                "4. Roadmap — последовательность из 8-15 битов от завязки до развязки."
                   "Большинство битов должны заканчиваться выбором игрока (target_choice: true) —"
                   "это ключевая механика интерактивности. Только первый бит и, опционально,"
                   "1-2 атмосферных/переходных бита могут быть без выбора."
                "5. Тон и стиль повествования."
                "Отвечай СТРОГО в формате JSON, соответствующего этой схеме"
                """
                {
                  "title": string,              // короткое цепляющее название истории, в духе жанра
                  "public_description": string, // 1-2 предложения без спойлеров, показывается пользователю в каталоге перед стартом
                  "tone": string,                // тон и стиль повествования, например: "драматичное тёмное фэнтези, слоуберн"
                  "characters": [
                    {
                      "name": string,           // имя персонажа
                      "role": string,           // роль в истории, например: "протагонист, наёмница" / "антагонист" / "любовный интерес"
                      "arc": string,            // как персонаж меняется по ходу истории, внутренняя трансформация
                      "voice_notes": string     // особенности речи и характера, чтобы диалоги были узнаваемыми и стилистически стабильными от бита к биту
                    }
                  ],
                  "roadmap": [
                    {
                      "id": integer,            // порядковый номер бита, начиная с 1
                      "title": string,          // короткое название этапа сюжета, например: "Завязка", "Первая встреча"
                      "goal": string,           // что именно происходит в этом бите — сюжетное событие, которое должно быть раскрыто
                      "target_choice": boolean, // true — бит должен закончиться выбором игрока; false — бит проходной/атмосферный, без выбора
                      "choice_stakes": string | null // если target_choice: true — в чём суть выбора и на что он влияет дальше по сюжету; если target_choice: false — null
                    }
                  ]
                }
                """
                "Правила по полям:"
                '- "characters": массив из 2-4 объектов.'
                '- "roadmap": массив из 8-15 объектов, id по порядку начиная с 1.'
                '- "choice_stakes" обязателен (непустая строка), если target_choice: true.'
            ),
        }
        user_promt = {"role": "user", "content": prompt}
        return [system_promt, user_promt]

    async def generator(self, user_prompt: str) -> Novel:
        """Генерация новелы"""
        prompt = await self.__create_promt(user_prompt)
        try:
            data = await self._generator.generate(prompt)
            logger.info("data: {}".format(data))
        except Exception as e:
            logger.error(e)
            raise NovelGenerationError(str(e)) from e

        novel = Novel(
            id=None,
            title=data['title'],
            public_description=data['public_description'],
            tone=data['tone'],
            created_at=None,
            updated_at=None,
        )
        novel = await self._novel_service.add(novel)

        characters = data['characters']
        for character_data in characters:
            character = Character(
                id=None,
                novel_id=novel.id,
                name=character_data['name'],
                role=character_data['role'],
                arc=character_data['arc'],
                voice_notes=character_data['voice_notes'],
                created_at=None,
                updated_at=None,
            )
            await self._character_service.add(character)

        roadmaps = data['roadmap']
        for roadmap_data in roadmaps:
            roadmap = Roadmap(
                id=None,
                novel_id=novel.id,
                step_id=roadmap_data['id'],
                title=roadmap_data['title'],
                goal=roadmap_data['goal'],
                target_choice=roadmap_data['target_choice'],
                choice_stakes=roadmap_data['choice_stakes'],
                created_at=None,
                updated_at=None,
            )
            await self._roadmap_service.add(roadmap)
        return novel

    def __find_neighbors(
        self, roadmaps: list[Roadmap], current: Roadmap
    ) -> tuple[Roadmap | None, Roadmap | None]:
        """Находит предыдущий и следующий шаг по step_id в отсортированном списке"""
        ordered = sorted(roadmaps, key=lambda r: r.step_id)
        index = next(i for i, r in enumerate(ordered) if r.id == current.id)

        previous_roadmap = ordered[index - 1] if index > 0 else None
        next_roadmap = ordered[index + 1] if index < len(ordered) - 1 else None
        return previous_roadmap, next_roadmap

    async def __create_dialogue_prompt(
        self,
        novel: Novel,
        characters: list[Character],
        previous_roadmap: Roadmap | None,
        current_roadmap: Roadmap,
        next_roadmap: Roadmap | None,
    ) -> list:
        characters_desc = "\n".join(
            f"- {c.name} ({c.role}): арка — {c.arc}; голос — {c.voice_notes}"
            for c in characters
        )

        context_parts = []
        if previous_roadmap:
            context_parts.append(f"Предыдущий бит: «{previous_roadmap.title}» — {previous_roadmap.goal}")
        else:
            context_parts.append("Это первый бит истории, до него ничего не было.")

        context_parts.append(
            f"Текущий бит (пиши диалоги ТОЛЬКО для него): «{current_roadmap.title}» — {current_roadmap.goal}"
        )

        if next_roadmap:
            context_parts.append(
                f"Следующий бит (только для ориентира, не пиши для него диалоги): "
                f"«{next_roadmap.title}» — {next_roadmap.goal}"
            )
        else:
            context_parts.append("Это последний бит истории.")

        choice_instruction = (
            f"Текущий бит ДОЛЖЕН закончиться выбором игрока. Суть выбора: {current_roadmap.choice_stakes}"
            if current_roadmap.target_choice
            else "Текущий бит НЕ должен заканчиваться выбором игрока — это проходной/атмосферный бит."
        )

        system_promt = {
            "role": "system",
            "content": (
                "Ты сценарист интерактивных визуальных новелл. "
                "Напиши диалоги для ОДНОГО бита истории, опираясь на контекст соседних битов и персонажей. "
                "Не пересказывай предыдущий бит и не забегай вперёд в следующий — только содержание текущего.\n\n"
                f"Тон и стиль новеллы: {novel.tone}\n\n"
                f"Персонажи:\n{characters_desc}\n\n"
                f"Контекст сюжета:\n{chr(10).join(context_parts)}\n\n"
                f"{choice_instruction}\n\n"
                "Правила:\n"
                "1. Каждая реплика — отдельный элемент dialogue_lines, order по возрастанию начиная с 0.\n"
                "2. Поле character — точное имя персонажа из списка выше, дословно.\n"
                "3. is_final_for_roadmap: true — только у последней реплики бита.\n"
                "4. Если бит с выбором — у финальной реплики actions содержит 2-4 варианта.\n"
                "5. Если бит без выбора — у финальной реплики actions — пустой массив.\n\n"
                "Отвечай СТРОГО в формате JSON по схеме:\n"
                """
                {
                  "dialogue_lines": [
                    {
                      "order": integer,
                      "character": string,
                      "text": string,
                      "is_final_for_roadmap": boolean,
                      "actions": [
                        { "order": integer, "text": string }
                      ]
                    }
                  ]
                }
                """
            ),
        }
        return [system_promt]

    async def start(self, novel_id: int, roadmap_id: int) -> list[DialogueLine]:
        """Генерация диалогов для конкретного шага roadmap новеллы"""
        novel = await self._novel_service.get(novel_id)
        if novel is None:
            raise NovelGenerationError(f"Novel {novel_id} not found")

        characters = await self._character_service.list_by_novel(novel_id)

        roadmaps = await self._roadmap_service.list_by_novel(novel_id)
        current_roadmap = next((r for r in roadmaps if r.id == roadmap_id), None)
        if current_roadmap is None:
            raise NovelGenerationError(f"Roadmap {roadmap_id} not found in novel {novel_id}")

        previous_roadmap, next_roadmap = self.__find_neighbors(roadmaps, current_roadmap)

        prompt = await self.__create_dialogue_prompt(
            novel, characters, previous_roadmap, current_roadmap, next_roadmap
        )

        try:
            data = await self._generator.generate(prompt)
            logger.info("dialogue data: {}".format(data))
        except Exception as e:
            logger.error(e)
            raise NovelGenerationError(str(e)) from e

        character_by_name = {c.name: c.id for c in characters}

        result = []
        for line_data in data["dialogue_lines"]:
            character_id = character_by_name.get(line_data["character"])
            if character_id is None:
                raise NovelGenerationError(f"Unknown character in dialogue: {line_data['character']}")

            dialogue_line = DialogueLine(
                id=None,
                novel_id=novel_id,
                roadmap_id=current_roadmap.id,
                character_id=character_id,
                order=line_data["order"],
                text=line_data["text"],
                is_final_for_roadmap=line_data["is_final_for_roadmap"],
                created_at=None,
                updated_at=None,
            )
            dialogue_line = await self._dialogue_line_service.add(dialogue_line)

            for action_data in line_data.get("actions", []):
                dialogue_action = DialogueAction(
                    id=None,
                    dialogue_line_id=dialogue_line.id,
                    order=action_data["order"],
                    text=action_data["text"],
                    next_roadmap_id=next_roadmap.id if next_roadmap else None,
                    created_at=None,
                    updated_at=None,
                )
                await self._dialogue_action_service.add(dialogue_action)

            result.append(dialogue_line)

        return result