from src.core.novels.services.crud import NovelCRUDService
from src.outbound.ai_plot.gateway import AiPlotGateway


async def get_novel_crud_service() -> NovelCRUDService:
    return NovelCRUDService(
        plot_generator=AiPlotGateway(),
    )
