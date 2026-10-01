from src.core.novels.interfaces import PlotGeneratorProtocol


class NovelCRUDService:

    def __init__(
        self,
        plot_generator: PlotGeneratorProtocol,
    ):
        self._plot_generator = plot_generator

    async def create(self, prompt: str, universe_id: int):
        await self._plot_generator.request_novel_generation(prompt, universe_id)
