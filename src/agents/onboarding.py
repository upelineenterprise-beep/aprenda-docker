import logging
from decimal import Decimal, InvalidOperation
from src.infrastructure import supabase_client, cache, evolution_client

logger = logging.getLogger(__name__)

PERGUNTAS = [
    ("name", "Olá! Sou o *Zé Calculei* 🪚\n\nVou te ajudar a gerar orçamentos profissionais pelo WhatsApp.\n\nPrimeiro, qual é o *nome da sua empresa ou marcenaria*?"),
    ("monthly_costs", "Ótimo! Agora me diz: qual é o total dos seus *custos fixos mensais* (aluguel, funcionários, luz, etc)?\n\nResponde só o valor, ex: _8500_"),
    ("working_days", "Quantos *dias por mês* você trabalha normalmente?\n\nEx: _22_"),
    ("tax_pct", "Qual a sua alíquota de *imposto* (%)?\n\nSe não tem ou não sabe, responde _0_"),
    ("margin_pct", "Que *margem de lucro* você quer colocar nos orçamentos (%)?\n\nEx: _30_ para 30%"),
    ("validity_days", "Por último: por quantos *dias* seu orçamento fica válido?\n\nEx: _10_"),
]

MENSAGEM_ERRO = "Ops, algo deu errado. Tenta novamente! 🙏"


async def iniciar_onboarding(phone: str) -> None:
    await cache.set_session(phone, {"state": "ONBOARDING", "data": {"step": 0}})
    await _enviar(phone, PERGUNTAS[0][1])


async def processar_onboarding(phone: str, texto: str) -> None:
    try:
        session = await cache.get_session(phone)
        data = session.get("data", {})
        step = data.get("step", 0)

        campo, _ = PERGUNTAS[step]
        valor = texto.strip()

        try:
            if campo == "name":
                if len(valor) < 2:
                    raise ValueError("Nome muito curto.")
                data[campo] = valor

            elif campo == "monthly_costs":
                valor_num = _parse_decimal(valor)
                if valor_num <= 0:
                    raise ValueError("Valor deve ser positivo.")
                data[campo] = float(valor_num)

            elif campo == "working_days":
                dias = int(valor)
                if dias <= 0 or dias > 31:
                    raise ValueError("Dias inválidos.")
                data[campo] = dias

            elif campo == "tax_pct":
                pct = _parse_decimal(valor)
                if pct < 0 or pct >= 100:
                    raise ValueError("Percentual inválido.")
                data[campo] = float(pct)

            elif campo == "margin_pct":
                pct = _parse_decimal(valor)
                if pct < 0 or pct >= 100:
                    raise ValueError("Percentual inválido.")
                data[campo] = float(pct)

            elif campo == "validity_days":
                dias = int(valor)
                if dias <= 0:
                    raise ValueError("Dias inválidos.")
                data[campo] = dias

        except (ValueError, InvalidOperation):
            await _enviar(phone, f"Valor inválido. Por favor, tenta novamente:\n\n{PERGUNTAS[step][1]}")
            return

        next_step = step + 1
        data["step"] = next_step
        await cache.set_session(phone, {"state": "ONBOARDING", "data": data})

        if next_step < len(PERGUNTAS):
            await _enviar(phone, PERGUNTAS[next_step][1])
        else:
            await _finalizar_onboarding(phone, data)

    except Exception as e:
        logger.error(f"Erro no onboarding {phone}: {e}", exc_info=True)
        await _enviar(phone, MENSAGEM_ERRO)


async def _finalizar_onboarding(phone: str, data: dict) -> None:
    empresa = await supabase_client.salvar_empresa(phone, data)
    if not empresa:
        await _enviar(phone, "Ocorreu um erro ao salvar seus dados. Por favor, tente novamente mais tarde.")
        await cache.clear_session(phone)
        return

    await cache.set_session(phone, {"state": "BUDGET_INPUT", "data": {}})
    await _enviar(
        phone,
        f"✅ *{data['name']}* cadastrada com sucesso!\n\n"
        "Agora é só me mandar os dados do projeto para eu gerar o orçamento.\n\n"
        "Pode mandar assim:\n"
        "_João Silva, suite e cozinha, 5 dias, material R$ 5.000_\n\n"
        "Ou com mais detalhes:\n"
        "_cliente Maria, closet + quarto, 4 dias, mat 4200, comissão 10%, parcelado em 3x_"
    )


def _parse_decimal(valor: str) -> Decimal:
    valor = valor.replace("R$", "").replace(".", "").replace(",", ".").strip()
    return Decimal(valor)


async def _enviar(phone: str, texto: str) -> None:
    await evolution_client.enviar_texto(phone, texto)
    try:
        await supabase_client.salvar_mensagem(phone, "OUT", texto)
    except Exception:
        pass
