"""
Gera o anexo da Etapa 2: como a ferramenta classificou os 30 fragmentos.

Uso:
    python experiments/anexo_resultado_fragmentos.py classificacao_ferramenta.csv anexo_etapa2.pdf
"""
import csv, sys
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer

ROTULO = {
    "LEMBRAR": "Lembrar", "ENTENDER": "Entender", "APLICAR": "Aplicar",
    "ANALISAR": "Analisar", "AVALIAR": "Avaliar", "CRIAR": "Criar",
    "SEM_VERBO_DOMINANTE": "Não classificado",
}

def main():
    entrada, saida = sys.argv[1], sys.argv[2]
    linhas = list(csv.DictReader(open(entrada, encoding="utf-8")))
    if len(linhas) != 30:
        print(f"AVISO: {len(linhas)} linhas, esperava 30.", file=sys.stderr)

    ss = getSampleStyleSheet()
    corpo = ParagraphStyle("corpo", parent=ss["Normal"], fontSize=8.5, leading=11)
    doc = SimpleDocTemplate(saida, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm,
                            title="Etapa 2 - Resultado da ferramenta")

    el = [Paragraph("<b>ANEXO — CLASSIFICAÇÃO PRODUZIDA PELA FERRAMENTA</b>", ss["Heading2"]),
          Paragraph("Abaixo, como a ferramenta classificou cada um dos 30 fragmentos da Etapa 1. "
                    "A numeração é a mesma do caderno anterior. "
                    "“Não classificado” indica que nenhum nível atingiu os critérios de densidade "
                    "mínima e dominância adotados pela ferramenta — é uma abstenção, não um erro de leitura.",
                    corpo),
          Spacer(1, 10)]

    dados = [["Nº", "Classificação da ferramenta", "Fragmento (início)"]]
    for l in linhas:
        dados.append([l["n"],
                      ROTULO.get(l["nivel_ferramenta"], l["nivel_ferramenta"]),
                      Paragraph(l["texto"][:150] + "...", corpo)])

    t = Table(dados, colWidths=[1.2*cm, 4.3*cm, 11*cm], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e8e8e8")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8.5),
        ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f6f6f6")]),
    ]))
    el.append(t)
    doc.build(el)
    print(f"{saida} gerado com {len(linhas)} fragmentos.")

if __name__ == "__main__":
    main()
