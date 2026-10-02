import httpx
from pydantic import ValidationError

from src.core.novel.exceptions import NovelNotFoundError, NovelProviderUnavailableError
from src.core.novel.interfaces import NovelProviderProtocol
from src.core.novel.models.novel import Novel, NovelPage
from src.core.novel.models.step import NovelStep
from src.outbound.ai_plot.schemas import AiPlotNovel, AiPlotNovelList, AiPlotNovelStep


class AiPlotNovelProvider(NovelProviderProtocol):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def get(self, novel_id: int) -> Novel:
        response = await self._request("GET", f"/novels/{novel_id}", novel_id)
        return AiPlotNovel.model_validate_json(response.content).to_domain()

    async def list(self, limit: int, offset: int) -> NovelPage:
        response = await self._request(
            "GET", "/novels/", params={"limit": limit, "offset": offset}
        )
        page = AiPlotNovelList.model_validate_json(response.content)
        return NovelPage(
            items=[item.to_domain() for item in page.items],
            total=page.total,
            limit=page.limit,
            offset=page.offset,
        )

    async def delete(self, novel_id: int) -> None:
        await self._request("DELETE", f"/novels/{novel_id}", novel_id)

    async def get_step(self, novel_id: int, offset: int | None) -> NovelStep:
        params = {"offset": offset} if offset is not None else None
        response = await self._request(
            "GET", f"/novels/start/{novel_id}", novel_id, params=params
        )
        try:
            return AiPlotNovelStep.model_validate_json(response.content).to_domain()
        except ValidationError as e:
            raise NovelProviderUnavailableError(
                f"ai_plot вернул неожиданный ответ шага: {e}"
            ) from e

    async def _request(
        self,
        method: str,
        url: str,
        novel_id: int | None = None,
        params: dict | None = None,
    ) -> httpx.Response:
        try:
            response = await self._client.request(method, url, params=params)
        except httpx.HTTPError as e:
            raise NovelProviderUnavailableError(str(e)) from e

        if response.status_code == 404 and novel_id is not None:
            raise NovelNotFoundError(novel_id)
        if response.is_error:
            raise NovelProviderUnavailableError(
                f"ai_plot {method} {url} -> {response.status_code}"
            )
        return response
