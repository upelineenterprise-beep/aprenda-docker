from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass


@dataclass
class ResultadoCalculo:
    custo_diario: Decimal
    base_custo: Decimal
    total_percentuais: Decimal
    preco_final: Decimal
    breakdown: dict


class ErroCalculoPrecificacao(Exception):
    pass


class PricingEngine:
    """Fórmula pura de precificação. Sem dependências externas."""

    def calcular(
        self,
        custos_fixos_mensais: Decimal,
        dias_trabalhados: int,
        dias_projeto: int,
        custo_material: Decimal,
        custo_deslocamento: Decimal = Decimal("0"),
        imposto_pct: Decimal = Decimal("0"),
        margem_pct: Decimal = Decimal("0"),
        comissao_pct: Decimal = Decimal("0"),
        juros_pct: Decimal = Decimal("0"),
    ) -> ResultadoCalculo:
        if dias_trabalhados <= 0:
            raise ErroCalculoPrecificacao("Dias trabalhados deve ser maior que zero.")

        if dias_projeto <= 0:
            raise ErroCalculoPrecificacao("Dias do projeto deve ser maior que zero.")

        total_pct = imposto_pct + margem_pct + comissao_pct + juros_pct
        if total_pct >= Decimal("100"):
            raise ErroCalculoPrecificacao(
                "Soma dos percentuais não pode ser maior ou igual a 100%."
            )

        custo_diario = custos_fixos_mensais / Decimal(dias_trabalhados)
        base_custo = (custo_diario * Decimal(dias_projeto)) + custo_material + custo_deslocamento
        divisor = Decimal("1") - (total_pct / Decimal("100"))
        preco_final = base_custo / divisor

        preco_final = preco_final.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        custo_diario = custo_diario.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        breakdown = {
            "custo_diario": custo_diario,
            "custo_mao_obra": (custo_diario * Decimal(dias_projeto)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            ),
            "custo_material": custo_material,
            "custo_deslocamento": custo_deslocamento,
            "base_custo": base_custo.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "imposto_pct": imposto_pct,
            "margem_pct": margem_pct,
            "comissao_pct": comissao_pct,
            "juros_pct": juros_pct,
            "total_percentuais": total_pct,
            "preco_final": preco_final,
        }

        return ResultadoCalculo(
            custo_diario=custo_diario,
            base_custo=base_custo.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            total_percentuais=total_pct,
            preco_final=preco_final,
            breakdown=breakdown,
        )
