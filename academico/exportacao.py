"""Exportação de relatórios em CSV e PDF (RF09)."""
import csv
import io
from typing import Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle


def gerar_csv(cabecalho: Sequence[str], linhas: Sequence[Sequence]) -> bytes:
    """CSV com separador ';' e BOM UTF-8, compatível com o Excel em pt-BR."""
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";")
    escritor.writerow(cabecalho)
    escritor.writerows(linhas)
    return ("\ufeff" + saida.getvalue()).encode("utf-8")


def gerar_pdf(titulo: str, cabecalho: Sequence[str], linhas: Sequence[Sequence]) -> bytes:
    """Relatório tabular em PDF (A4) com ReportLab."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=titulo)
    estilos = getSampleStyleSheet()
    dados = [list(cabecalho)] + [[str(c) for c in l] for l in linhas]
    tabela = Table(dados, repeatRows=1)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    doc.build([Paragraph(titulo, estilos["Title"]), tabela])
    return buffer.getvalue()
