import json
import logging
from typing import Optional
import redis.asyncio as aioredis
from src.config import settings

logger = logging.getLogger(__name__)

_client: Optional[aioredis.Redis] = None

SESSION_TTL = 3600 * 24  # 24 horas


def get_client() -> aioredis.Redis:
    global _client
    if _client is None:
        _client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


async def get_session(phone: str) -> dict:
    try:
        client = get_client()
        data = await client.get(f"session:{phone}")
        if data:
            return json.loads(data)
        return {"state": "IDLE", "data": {}}
    except Exception as e:
        logger.error(f"Erro ao buscar sessão {phone}: {e}")
        return {"state": "IDLE", "data": {}}


async def set_session(phone: str, session: dict) -> None:
    try:
        client = get_client()
        await client.setex(f"session:{phone}", SESSION_TTL, json.dumps(session, default=str))
    except Exception as e:
        logger.error(f"Erro ao salvar sessão {phone}: {e}")


async def clear_session(phone: str) -> None:
    try:
        client = get_client()
        await client.delete(f"session:{phone}")
    except Exception as e:
        logger.error(f"Erro ao limpar sessão {phone}: {e}")


async def set_state(phone: str, state: str) -> None:
    session = await get_session(phone)
    session["state"] = state
    await set_session(phone, session)


async def get_state(phone: str) -> str:
    session = await get_session(phone)
    return session.get("state", "IDLE")


async def update_session_data(phone: str, updates: dict) -> None:
    session = await get_session(phone)
    session["data"].update(updates)
    await set_session(phone, session)


async def get_session_data(phone: str) -> dict:
    session = await get_session(phone)
    return session.get("data", {})
