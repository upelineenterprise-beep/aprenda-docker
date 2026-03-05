import io
import logging
from datetime import date, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

logger = logging.getLogger(__name__)


def _fmt(v) -> str:
    return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def gerar_pdf_orcamento(company: dict, budget_data: dict, resultado) -> bytes:
    """Gera PDF do orçamento e retorna bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    elements = []

    cor_primaria = colors.HexColor("#1a1a2e")
    cor_destaque = colors.HexColor("#e94560")
    cor_cinza = colors.HexColor("#f5f5f5")

    style_empresa = ParagraphStyle("empresa", parent=styles["Heading1"], fontSize=22, textColor=cor_primaria, spaceAfter=4)
    style_subtitulo = ParagraphStyle("subtitulo", parent=styles["Normal"], fontSize=10, textColor=colors.grey, spaceAfter=2)
    style_secao = ParagraphStyle("secao", parent=styles["Heading2"], fontSize=12, textColor=cor_primaria, spaceBefore=12, spaceAfter=6)
    style_titulo_orc = ParagraphStyle("titulo_orc", parent=styles["Heading1"], fontSize=16, textColor=cor_destaque, spaceAfter=6)
    style_rodape = ParagraphStyle("rodape", parent=styles["Normal"], fontSize=9, textColor=colors.grey)

    # Cabeçalho
    elements.append(Paragraph(company["name"], style_empresa))
    if company.get("email"):
        elements.append(Paragraph(company["email"], style_subtitulo))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(HRFlowable(width="100%", thickness=2, color=cor_destaque))
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("ORÇAMENTO", style_titulo_orc))

    # Dados do cliente
    elements.append(Paragraph("Dados do Cliente", style_secao))
    data_cliente = [
        ["Cliente:", budget_data.get("client_name", "—")],
        ["Ambientes:", budget_data.get("environments", "—")],
        ["Prazo de execução:", f"{budget_data.get('project_days', 0)} dias úteis"],
        ["Pagamento:", budget_data.get("payment_type", "avista").title()],
    ]
    if budget_data.get("payment_type") == "parcelado":
        data_cliente.append(["Parcelas:", f"{budget_data.get('installments', 1)}x"])

    table_cliente = Table(data_cliente, colWidths=[4 * cm, 12 * cm])
    table_cliente.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, cor_cinza]),
    ]))
    elements.append(table_cliente)

    # Breakdown
    elements.append(Paragraph("Composição do Preço", style_secao))
    bd = resultado.breakdown

    data_breakdown = [
        ["Item", "Valor"],
        ["Mão de obra", _fmt(bd["custo_mao_obra"])],
        ["Material", _fmt(bd["custo_material"])],
    ]
    if bd["custo_deslocamento"] > 0:
        data_breakdown.append(["Deslocamento", _fmt(bd["custo_deslocamento"])])
    data_breakdown.append(["Base de custo", _fmt(bd["base_custo"])])
    data_breakdown.append(["", ""])
    for label, key in [("Impostos", "imposto_pct"), ("Margem de lucro", "margem_pct"), ("Comissão", "comissao_pct"), ("Juros", "juros_pct")]:
        if bd[key] > 0:
            data_breakdown.append([f"{label} ({bd[key]}%)", "incluso"])

    table_bd = Table(data_breakdown, colWidths=[11 * cm, 5 * cm])
    table_bd.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), cor_primaria),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, cor_cinza]),
        ("LINEBELOW", (0, 0), (-1, 0), 1, cor_primaria),
    ]))
    elements.append(table_bd)

    # Total
    elements.append(Spacer(1, 0.5 * cm))
    table_total = Table([["TOTAL DO ORÇAMENTO", _fmt(bd["preco_final"])]], colWidths=[11 * cm, 5 * cm])
    table_total.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), cor_destaque),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 14),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (0, -1), 12),
    ]))
    elements.append(table_total)

    # Validade
    elements.append(Spacer(1, 1 * cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    elements.append(Spacer(1, 0.3 * cm))
    validade = date.today() + timedelta(days=int(company.get("validity_days", 10)))
    elements.append(Paragraph(
        f"Este orçamento é válido até {validade.strftime('%d/%m/%Y')}. Gerado pelo Zé Calculei.",
        style_rodape,
    ))

    doc.build(elements)
    return buffer.getvalue()
