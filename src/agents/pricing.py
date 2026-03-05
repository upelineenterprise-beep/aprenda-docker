import logging
from decimal import Decimal
from src.domain.pricing_engine import PricingEngine, ResultadoCalculo

logger = logging.getLogger(__name__)

_engine = PricingEngine()


async def calcular_preco(empresa: dict, budget_data: dict) -> ResultadoCalculo:
    """Aplica a fórmula de precificação com os dados da empresa e do projeto."""
    resultado = _engine.calcular(
        custos_fixos_mensais=Decimal(str(empresa["monthly_costs"])),
        dias_trabalhados=int(empresa["working_days"]),
        dias_projeto=int(budget_data["project_days"]),
        custo_material=Decimal(str(budget_data.get("material_cost", 0))),
        custo_deslocamento=Decimal(str(budget_data.get("displacement_cost", 0))),
        imposto_pct=Decimal(str(empresa.get("tax_pct", 0))),
        margem_pct=Decimal(str(empresa.get("margin_pct", 0))),
        comissao_pct=Decimal(str(budget_data.get("commission_pct", 0) or 0)),
        juros_pct=Decimal(str(budget_data.get("interest_pct", 0) or 0)),
    )
    logger.info(f"Preço calculado: R$ {resultado.preco_final}")
    return resultado
