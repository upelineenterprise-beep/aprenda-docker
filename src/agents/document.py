import logging
from src.infrastructure.pdf_generator import gerar_pdf_orcamento
from src.domain.pricing_engine import ResultadoCalculo

logger = logging.getLogger(__name__)


async def gerar_documento(empresa: dict, budget_data: dict, resultado: ResultadoCalculo) -> bytes:
    """Gera o PDF do orçamento e retorna os bytes."""
    try:
        pdf_bytes = gerar_pdf_orcamento(empresa, budget_data, resultado)
        logger.info(f"PDF gerado: {len(pdf_bytes)} bytes para empresa {empresa.get('phone')}")
        return pdf_bytes
    except Exception as e:
        logger.error(f"Erro ao gerar PDF: {e}", exc_info=True)
        raise
