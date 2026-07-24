from src.core.novels.exceptions import NovelNotFoundError, NovelGenerationError
from src.core.novels.interfaces import NovelRepositoryProtocol, NovelGeneratorProtocol
from src.core.novels.models import Novel


class NovelService:
    def __init__(
        self,
        repository: NovelRepositoryProtocol,
        generator: NovelGeneratorProtocol,
    ):
        self._repository = repository
        self._generator = generator

    async def __promt(self, prompt: str) -> list:
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

    async def create_novel(self, user_prompt: str) -> Novel:
        prompt = await self.__promt(user_prompt)
        try:
            title, description = await self._generator.generate(prompt)
        except Exception as e:
            print(e)
            raise NovelGenerationError(str(e)) from e

        novel = Novel(id=None, title=title, description=description, created_at=None, updated_at=None)
        return await self._repository.add(novel)

    async def get_novel(self, novel_id: int) -> Novel:
        novel = await self._repository.get_by_id(novel_id)
        if novel is None:
            raise NovelNotFoundError(novel_id)
        return novel

    async def list_novels(self) -> list[Novel]:
        return await self._repository.list_all()

    async def delete_novel(self, novel_id: int) -> None:
        await self._repository.delete(novel_id)