import logging
import httpx
from src.config import settings

logger = logging.getLogger(__name__)


async def enviar_texto(phone: str, mensagem: str) -> bool:
    """Envia mensagem de texto pelo WhatsApp via Evolution API."""
    url = f"{settings.EVOLUTION_API_URL}/message/sendText/{settings.EVOLUTION_INSTANCE}"
    headers = {"apikey": settings.EVOLUTION_API_KEY, "Content-Type": "application/json"}
    payload = {
        "number": phone,
        "text": mensagem,
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return True
    except httpx.HTTPStatusError as e:
        logger.error(f"Erro HTTP ao enviar texto para {phone}: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"Erro ao enviar texto para {phone}: {e}")
        return False


async def enviar_documento(phone: str, pdf_bytes: bytes, filename: str, caption: str = "") -> bool:
    """Envia PDF pelo WhatsApp via Evolution API."""
    import base64
    url = f"{settings.EVOLUTION_API_URL}/message/sendMedia/{settings.EVOLUTION_INSTANCE}"
    headers = {"apikey": settings.EVOLUTION_API_KEY, "Content-Type": "application/json"}
    payload = {
        "number": phone,
        "mediatype": "document",
        "mimetype": "application/pdf",
        "caption": caption,
        "media": base64.b64encode(pdf_bytes).decode("utf-8"),
        "fileName": filename,
    }
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return True
    except httpx.HTTPStatusError as e:
        logger.error(f"Erro HTTP ao enviar doc para {phone}: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        logger.error(f"Erro ao enviar documento para {phone}: {e}")
        return False
