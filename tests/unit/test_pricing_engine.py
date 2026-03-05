import pytest
from decimal import Decimal
from src.domain.pricing_engine import PricingEngine, ErroCalculoPrecificacao


@pytest.fixture
def engine():
    return PricingEngine()


def test_custo_diario_correto(engine):
    resultado = engine.calcular(
        custos_fixos_mensais=Decimal("10000"),
        dias_trabalhados=22,
        dias_projeto=5,
        custo_material=Decimal("5000"),
    )
    assert resultado.custo_diario == Decimal("454.55")


def test_preco_final_exemplo_real(engine):
    """Exemplo real: R$ 13.722,07"""
    resultado = engine.calcular(
        custos_fixos_mensais=Decimal("10000"),
        dias_trabalhados=22,
        dias_projeto=5,
        custo_material=Decimal("5000"),
        custo_deslocamento=Decimal("0"),
        imposto_pct=Decimal("6"),
        margem_pct=Decimal("30"),
        comissao_pct=Decimal("10"),
        juros_pct=Decimal("1"),
    )
    assert resultado.preco_final == Decimal("13722.07")


def test_erro_dias_trabalhados_zero(engine):
    with pytest.raises(ErroCalculoPrecificacao, match="Dias trabalhados deve ser maior que zero"):
        engine.calcular(
            custos_fixos_mensais=Decimal("10000"),
            dias_trabalhados=0,
            dias_projeto=5,
            custo_material=Decimal("5000"),
        )


def test_erro_dias_projeto_zero(engine):
    with pytest.raises(ErroCalculoPrecificacao, match="Dias do projeto deve ser maior que zero"):
        engine.calcular(
            custos_fixos_mensais=Decimal("10000"),
            dias_trabalhados=22,
            dias_projeto=0,
            custo_material=Decimal("5000"),
        )


def test_erro_percentuais_iguais_100(engine):
    with pytest.raises(ErroCalculoPrecificacao, match="Soma dos percentuais"):
        engine.calcular(
            custos_fixos_mensais=Decimal("10000"),
            dias_trabalhados=22,
            dias_projeto=5,
            custo_material=Decimal("5000"),
            imposto_pct=Decimal("50"),
            margem_pct=Decimal("50"),
        )


def test_erro_percentuais_acima_100(engine):
    with pytest.raises(ErroCalculoPrecificacao):
        engine.calcular(
            custos_fixos_mensais=Decimal("10000"),
            dias_trabalhados=22,
            dias_projeto=5,
            custo_material=Decimal("5000"),
            margem_pct=Decimal("101"),
        )


def test_breakdown_campos_presentes(engine):
    resultado = engine.calcular(
        custos_fixos_mensais=Decimal("10000"),
        dias_trabalhados=22,
        dias_projeto=5,
        custo_material=Decimal("5000"),
        imposto_pct=Decimal("6"),
        margem_pct=Decimal("30"),
        comissao_pct=Decimal("10"),
        juros_pct=Decimal("1"),
    )
    bd = resultado.breakdown
    assert "custo_diario" in bd
    assert "custo_mao_obra" in bd
    assert "custo_material" in bd
    assert "base_custo" in bd
    assert "preco_final" in bd
    assert bd["custo_material"] == Decimal("5000")
    assert bd["imposto_pct"] == Decimal("6")
    assert bd["margem_pct"] == Decimal("30")


def test_sem_percentuais(engine):
    resultado = engine.calcular(
        custos_fixos_mensais=Decimal("10000"),
        dias_trabalhados=22,
        dias_projeto=1,
        custo_material=Decimal("0"),
    )
    assert resultado.preco_final == resultado.base_custo


def test_com_deslocamento(engine):
    resultado_sem = engine.calcular(
        custos_fixos_mensais=Decimal("10000"),
        dias_trabalhados=22,
        dias_projeto=5,
        custo_material=Decimal("5000"),
    )
    resultado_com = engine.calcular(
        custos_fixos_mensais=Decimal("10000"),
        dias_trabalhados=22,
        dias_projeto=5,
        custo_material=Decimal("5000"),
        custo_deslocamento=Decimal("500"),
    )
    assert resultado_com.preco_final > resultado_sem.preco_final
