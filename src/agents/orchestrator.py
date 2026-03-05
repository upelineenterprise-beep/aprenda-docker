import logging
from src.infrastructure import supabase_client, cache, evolution_client

logger = logging.getLogger(__name__)

MENSAGEM_ERRO = "Ops, algo deu errado por aqui. Tenta novamente em instantes! 🙏"


async def processar_mensagem(phone: str, texto: str) -> None:
    """Ponto de entrada principal. Recebe a mensagem e roteia para o agente correto."""
    try:
        await supabase_client.salvar_mensagem(phone, "IN", texto)
    except Exception as e:
        logger.error(f"Erro ao logar mensagem de entrada {phone}: {e}")

    try:
        state = await cache.get_state(phone)
        logger.info(f"[{phone}] estado={state} mensagem={texto[:50]}")

        if state == "ONBOARDING":
            from src.agents.onboarding import processar_onboarding
            await processar_onboarding(phone, texto)
            return

        if state in ("BUDGET_INPUT", "BUDGET_CONFIRM"):
            from src.agents.parser import processar_parser
            await processar_parser(phone, texto)
            return

        if state == "GENERATING":
            await _enviar(phone, "Aguarda um momento, ainda estou gerando seu orçamento... ⏳")
            return

        # IDLE — verifica se empresa está cadastrada
        empresa = await supabase_client.buscar_empresa(phone)
        if not empresa:
            await cache.set_state(phone, "ONBOARDING")
            from src.agents.onboarding import iniciar_onboarding
            await iniciar_onboarding(phone)
        else:
            await cache.set_state(phone, "BUDGET_INPUT")
            from src.agents.parser import processar_parser
            await processar_parser(phone, texto)

    except Exception as e:
        logger.error(f"Erro no orchestrator para {phone}: {e}", exc_info=True)
        await _enviar(phone, MENSAGEM_ERRO)


async def _enviar(phone: str, texto: str) -> None:
    ok = await evolution_client.enviar_texto(phone, texto)
    if ok:
        try:
            await supabase_client.salvar_mensagem(phone, "OUT", texto)
        except Exception:
            pass
