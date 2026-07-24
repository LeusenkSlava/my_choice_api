import json

from openai import APIError, APIConnectionError
from openai import AsyncOpenAI


class DeepSeekNovelGenerator:
    def __init__(self, client: AsyncOpenAI):
        self._client = client

    async def generate_j(self, prompt: list) -> tuple[str, str]:
        try:
            response = await self._client.chat.completions.create(
                model="deepseek-v4-flash",
                messages=prompt,
                response_format={"type": "json_object"},
                temperature=0.9,
            )
        except (APIError, APIConnectionError) as e:
            raise RuntimeError(f"DeepSeek API error: {e}") from e

        content = response.choices[0].message.content
        try:
            data = json.loads(content)
            return data["title"], data["description"]
        except (json.JSONDecodeError, KeyError) as e:
            raise RuntimeError(f"Invalid DeepSeek response format: {e}") from e
