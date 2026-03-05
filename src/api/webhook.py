import logging
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from src.agents.orchestrator import processar_mensagem

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/webhook/whatsapp")
async def webhook_whatsapp(request: Request, background_tasks: BackgroundTasks):
    """Recebe webhooks da Evolution API."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido")

    try:
        event = body.get("event", "")
        data = body.get("data", {})

        if event != "messages.upsert":
            return {"status": "ignored", "event": event}

        message = data.get("message", {})
        key = data.get("key", {})

        # Ignora mensagens enviadas pelo próprio bot
        if key.get("fromMe"):
            return {"status": "ignored", "reason": "fromMe"}

        phone = key.get("remoteJid", "").replace("@s.whatsapp.net", "").replace("@g.us", "")
        if not phone:
            return {"status": "ignored", "reason": "no_phone"}

        # Extrai texto da mensagem
        texto = (
            message.get("conversation")
            or message.get("extendedTextMessage", {}).get("text")
            or ""
        ).strip()

        if not texto:
            return {"status": "ignored", "reason": "no_text"}

        background_tasks.add_task(processar_mensagem, phone, texto)
        return {"status": "queued", "phone": phone}

    except Exception as e:
        logger.error(f"Erro no webhook: {e}", exc_info=True)
        return {"status": "error", "detail": str(e)}
