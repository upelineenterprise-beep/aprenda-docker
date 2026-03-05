import logging
from openai import AsyncOpenAI
from src.config import settings

logger = logging.getLogger(__name__)

_client: AsyncOpenAI = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def chat_completion(system_prompt: str, user_message: str, temperature: float = 0.2) -> str:
    try:
        client = get_client()
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Erro na chamada OpenAI: {e}")
        raise
