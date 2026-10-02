import httpx

from src.main.config.settings import settings


def build_ai_plot_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.ai_plot.BASE_URL,
        timeout=settings.ai_plot.TIMEOUT,
    )
