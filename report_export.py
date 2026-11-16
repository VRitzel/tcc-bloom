import csv
import logging

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from analysis import BLOOM_ORDER

log = logging.getLogger("genese")


def _dominant_level_and_density(topic):
    bloom_map = topic.get("bloom_level", {})
    if not bloom_map or all(density == 0.0 for density in bloom_map.values()):
        return "N/A", 0.0
    dominant_level = max(bloom_map, key=bloom_map.get)
    return dominant_level, bloom_map[dominant_level]


def export_to_csv(learning_path, file_path):
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Posição", "Nível Bloom", "Densidade (%)", "Título"])

        for topic in learning_path:
            dominant_level, density = _dominant_level_and_density(topic)
            writer.writerow([
                topic.get("path_position", "N/A"),
                dominant_level,
                density,
                topic.get("title", "N/A"),
            ])

    log.info(f"Relatório CSV exportado para {file_path}")


def export_to_pdf(learning_path, report, file_path):
    doc = SimpleDocTemplate(file_path, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Relatório do Roteiro de Aprendizagem", styles["Title"]))
    elements.append(Spacer(1, 0.5 * cm))

    elements.append(Paragraph("Distribuição por Nível Cognitivo (Taxonomia de Bloom)", styles["Heading2"]))
    distribution_rows = [["Nível", "Contagem", "Percentual"]]
    for level, order in sorted(BLOOM_ORDER.items(), key=lambda item: item[1]):
        count = report["distribution"].get(level, 0)
        percentage = report["percentages"].get(level, 0.0)
        distribution_rows.append([f"N{order} · {level}", str(count), f"{percentage}%"])
    distribution_rows.append(["Sem verbo dominante", str(report["unclassified_count"]), "-"])

    distribution_table = Table(distribution_rows, colWidths=[7 * cm, 4 * cm, 4 * cm])
    distribution_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
    ]))
    elements.append(distribution_table)
    elements.append(Spacer(1, 0.5 * cm))

    elements.append(Paragraph("Lacunas na Progressão Pedagógica", styles["Heading2"]))
    if report["missing_levels"]:
        missing_text = ", ".join(
            f"Nível {BLOOM_ORDER[level]} ({level})" for level in report["missing_levels"]
        )
        elements.append(Paragraph(
            f"O material não apresenta tópicos classificados nos seguintes níveis: {missing_text}.",
            styles["Normal"]
        ))
    else:
        elements.append(Paragraph(
            "O material apresenta tópicos em todos os níveis cognitivos da Taxonomia de Bloom.",
            styles["Normal"]
        ))
    elements.append(Spacer(1, 0.5 * cm))

    elements.append(Paragraph("Roteiro de Aprendizagem Ordenado", styles["Heading2"]))
    path_rows = [["#", "Nível Bloom", "Título"]]
    for topic in learning_path:
        dominant_level, _ = _dominant_level_and_density(topic)
        level_label = dominant_level if dominant_level == "N/A" else f"N{BLOOM_ORDER[dominant_level]} · {dominant_level}"
        path_rows.append([
            str(topic.get("path_position", "N/A")),
            level_label,
            topic.get("title", "N/A"),
        ])

    path_table = Table(path_rows, colWidths=[1.5 * cm, 4 * cm, 9.5 * cm], repeatRows=1)
    path_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(path_table)

    doc.build(elements)
    log.info(f"Relatório PDF exportado para {file_path}")
