import logging
from decimal import Decimal
from src.infrastructure import evolution_client, supabase_client
from src.domain.pricing_engine import ResultadoCalculo

logger = logging.getLogger(__name__)


def _fmt(v) -> str:
    return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


async def enviar_orcamento(phone: str, pdf_bytes: bytes, budget_data: dict, resultado: ResultadoCalculo) -> None:
    """Envia texto com resumo e o PDF pelo WhatsApp."""
    client_name = budget_data.get("client_name", "Cliente")
    payment = budget_data.get("payment_type", "avista")
    parcelas = budget_data.get("installments", 1)

    if payment == "parcelado" and parcelas > 1:
        valor_parcela = resultado.preco_final / Decimal(str(parcelas))
        info_pagamento = f"💳 {parcelas}x de {_fmt(valor_parcela)}"
    else:
        info_pagamento = f"💵 À vista: {_fmt(resultado.preco_final)}"

    mensagem = (
        f"🪚 *Orçamento gerado para {client_name}!*\n\n"
        f"🏠 Ambientes: {budget_data.get('environments', '—')}\n"
        f"📅 Prazo: {budget_data.get('project_days', 0)} dias úteis\n"
        f"💰 Material: {_fmt(resultado.breakdown['custo_material'])}\n"
        f"👷 Mão de obra: {_fmt(resultado.breakdown['custo_mao_obra'])}\n\n"
        f"💲 *TOTAL: {_fmt(resultado.preco_final)}*\n"
        f"{info_pagamento}\n\n"
        f"O PDF completo está logo abaixo 👇"
    )

    texto_ok = await evolution_client.enviar_texto(phone, mensagem)
    if not texto_ok:
        logger.warning(f"Falha ao enviar texto do orçamento para {phone}")

    filename = f"orcamento_{client_name.replace(' ', '_').lower()}.pdf"
    pdf_ok = await evolution_client.enviar_documento(
        phone, pdf_bytes, filename, caption=f"Orçamento - {client_name}"
    )
    if not pdf_ok:
        logger.error(f"Falha ao enviar PDF para {phone}")
        await evolution_client.enviar_texto(
            phone, "Não consegui enviar o PDF agora. Tenta pedir novamente em instantes."
        )

    try:
        await supabase_client.salvar_mensagem(phone, "OUT", mensagem)
    except Exception:
        pass
