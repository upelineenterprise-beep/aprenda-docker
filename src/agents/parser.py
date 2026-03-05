import json
import logging
from src.infrastructure import supabase_client, cache, evolution_client, openai_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é um assistente especializado em extrair dados de orçamentos de marcenaria a partir de mensagens informais em português brasileiro.

Extraia os dados e retorne APENAS um JSON válido com os campos abaixo. Use null para campos não informados.

Campos:
- client_name: string — nome do cliente
- environments: string — ambientes/cômodos (ex: "Suite casal e closet")
- project_days: integer — dias de trabalho do projeto
- material_cost: float — custo do material em reais
- displacement_cost: float — custo de deslocamento (default 0)
- commission_pct: float — percentual de comissão (ex: 10 para 10%)
- interest_pct: float — percentual de juros (ex: 1 para 1%)
- payment_type: string — "avista" ou "parcelado"
- installments: integer — número de parcelas (1 se à vista)

Exemplos de entrada → saída:
"orçamento pra João, suite e cozinha, 5 dias, material 5 conto"
→ {"client_name":"João","environments":"Suite e cozinha","project_days":5,"material_cost":5000.0,"displacement_cost":0,"commission_pct":null,"interest_pct":null,"payment_type":"avista","installments":1}

"cliente Maria, 3 ambientes, semana de trabalho, material 3500 à vista"
→ {"client_name":"Maria","environments":"3 ambientes","project_days":5,"material_cost":3500.0,"displacement_cost":0,"commission_pct":null,"interest_pct":null,"payment_type":"avista","installments":1}

"João Silva, closet + quarto, 4 dias, mat R$4.200, comissão 10%, parcelado em 3x"
→ {"client_name":"João Silva","environments":"Closet e quarto","project_days":4,"material_cost":4200.0,"displacement_cost":0,"commission_pct":10.0,"interest_pct":null,"payment_type":"parcelado","installments":3}

Retorne SOMENTE o JSON, sem texto adicional."""

CAMPOS_OBRIGATORIOS = ["client_name", "environments", "project_days", "material_cost"]

MENSAGEM_AGUARDANDO = (
    "Entendi! Ainda preciso de:\n"
    "{campos}\n\n"
    "Pode completar com esses dados?"
)

MENSAGEM_CONFIRMACAO = (
    "✅ *Confirma os dados do orçamento?*\n\n"
    "👤 Cliente: {client_name}\n"
    "🏠 Ambientes: {environments}\n"
    "📅 Dias de trabalho: {project_days}\n"
    "💰 Material: R$ {material_cost}\n"
    "🚗 Deslocamento: R$ {displacement_cost}\n"
    "📊 Comissão: {commission_pct}%\n"
    "💳 Juros: {interest_pct}%\n"
    "💵 Pagamento: {payment_type}\n"
    "{parcelas}"
    "\nResponde *sim* para gerar ou manda os dados corrigidos."
)


async def processar_parser(phone: str, texto: str) -> None:
    try:
        state = await cache.get_state(phone)

        # Confirmação pendente
        if state == "BUDGET_CONFIRM":
            if texto.strip().lower() in ("sim", "s", "yes", "confirma", "ok", "pode"):
                await _gerar_orcamento(phone)
            else:
                await cache.set_state(phone, "BUDGET_INPUT")
                await _enviar(phone, "Ok, me manda os dados corrigidos então.")
            return

        # Extrai dados com GPT
        try:
            resposta = await openai_client.chat_completion(SYSTEM_PROMPT, texto)
            dados_extraidos = json.loads(resposta)
        except Exception as e:
            logger.error(f"Erro ao parsear resposta OpenAI para {phone}: {e}")
            await _enviar(phone, "Não consegui entender os dados. Tenta assim:\n_João Silva, suite e cozinha, 5 dias, material R$ 5.000_")
            return

        # Acumula na sessão
        session_data = await cache.get_session_data(phone)
        for campo, valor in dados_extraidos.items():
            if valor is not None:
                session_data[campo] = valor

        await cache.update_session_data(phone, session_data)

        # Verifica campos obrigatórios faltando
        faltando = [c for c in CAMPOS_OBRIGATORIOS if not session_data.get(c)]
        if faltando:
            labels = {
                "client_name": "• Nome do cliente",
                "environments": "• Ambientes/cômodos",
                "project_days": "• Dias de trabalho",
                "material_cost": "• Custo do material (R$)",
            }
            lista = "\n".join(labels[c] for c in faltando)
            await _enviar(phone, MENSAGEM_AGUARDANDO.format(campos=lista))
            return

        # Tem tudo — pede confirmação
        d = session_data
        parcelas = f"🔢 Parcelas: {d.get('installments', 1)}x\n" if d.get("payment_type") == "parcelado" else ""
        msg = MENSAGEM_CONFIRMACAO.format(
            client_name=d.get("client_name", "—"),
            environments=d.get("environments", "—"),
            project_days=d.get("project_days", 0),
            material_cost=f"{float(d.get('material_cost', 0)):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            displacement_cost=f"{float(d.get('displacement_cost', 0)):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            commission_pct=d.get("commission_pct", 0) or 0,
            interest_pct=d.get("interest_pct", 0) or 0,
            payment_type=d.get("payment_type", "avista"),
            parcelas=parcelas,
        )
        await cache.set_state(phone, "BUDGET_CONFIRM")
        await _enviar(phone, msg)

    except Exception as e:
        logger.error(f"Erro no parser para {phone}: {e}", exc_info=True)
        await _enviar(phone, "Ops, algo deu errado. Tenta novamente! 🙏")


async def _gerar_orcamento(phone: str) -> None:
    from src.agents.pricing import calcular_preco
    from src.agents.document import gerar_documento
    from src.agents.notification import enviar_orcamento

    await cache.set_state(phone, "GENERATING")
    await _enviar(phone, "Perfeito! Gerando seu orçamento... ⏳")

    try:
        session_data = await cache.get_session_data(phone)
        empresa = await supabase_client.buscar_empresa(phone)

        resultado = await calcular_preco(empresa, session_data)
        pdf_bytes = await gerar_documento(empresa, session_data, resultado)
        await enviar_orcamento(phone, pdf_bytes, session_data, resultado)

        budget_id = await supabase_client.salvar_orcamento(phone, {
            **session_data,
            "final_price": float(resultado.preco_final),
            "daily_cost": float(resultado.custo_diario),
            "status": "done",
        })
        logger.info(f"Orçamento {budget_id} gerado para {phone}")

    except Exception as e:
        logger.error(f"Erro ao gerar orçamento para {phone}: {e}", exc_info=True)
        await _enviar(phone, "Erro ao gerar o orçamento. Tenta novamente em instantes! 😕")
        await supabase_client.salvar_mensagem(phone, "OUT", "ERRO_ORCAMENTO", str(e))
    finally:
        await cache.set_session(phone, {"state": "BUDGET_INPUT", "data": {}})


async def _enviar(phone: str, texto: str) -> None:
    await evolution_client.enviar_texto(phone, texto)
    try:
        await supabase_client.salvar_mensagem(phone, "OUT", texto)
    except Exception:
        pass
