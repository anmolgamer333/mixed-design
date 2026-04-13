import csv
from io import BytesIO, StringIO
from pathlib import Path
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.models.mix import MixDesign


EXPORT_DIR = Path("generated/exports")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def mix_table_rows(mix: MixDesign) -> list[dict[str, str | float]]:
    return [
        {"Parameter": "Mix ID", "Symbol": "-", "Value": mix.mix_id, "Unit": "-", "Remarks": "Unique identifier"},
        {"Parameter": "Grade of concrete", "Symbol": "fck", "Value": mix.concrete_grade, "Unit": "-", "Remarks": "Specified grade"},
        {"Parameter": "Target mean strength", "Symbol": "f'cm", "Value": mix.target_mean_strength, "Unit": "MPa", "Remarks": "Design target"},
        {"Parameter": "Water-cement ratio", "Symbol": "w/c", "Value": mix.water_cement_ratio, "Unit": "-", "Remarks": "Durability/performance control"},
        {"Parameter": "Water content", "Symbol": "W", "Value": mix.water_content_kg_m3, "Unit": "kg/m3", "Remarks": "Base water demand"},
        {"Parameter": "Cement content", "Symbol": "C", "Value": mix.cement_content_kg_m3, "Unit": "kg/m3", "Remarks": "Derived from w/c"},
        {"Parameter": "Fine aggregate quantity", "Symbol": "FA", "Value": mix.fine_agg_content_kg_m3, "Unit": "kg/m3", "Remarks": "SSD basis"},
        {"Parameter": "Coarse aggregate quantity", "Symbol": "CA", "Value": mix.coarse_agg_content_kg_m3, "Unit": "kg/m3", "Remarks": "SSD basis"},
        {"Parameter": "Admixture dosage", "Symbol": "Adm", "Value": mix.admixture_dosage_pct, "Unit": "% cement", "Remarks": mix.admixture_type},
        {"Parameter": "Moisture correction (fine)", "Symbol": "MCf", "Value": mix.moisture_correction_fine_pct, "Unit": "%", "Remarks": "Field correction"},
        {"Parameter": "Moisture correction (coarse)", "Symbol": "MCc", "Value": mix.moisture_correction_coarse_pct, "Unit": "%", "Remarks": "Field correction"},
        {"Parameter": "Water adjustment", "Symbol": "Wadj", "Value": mix.field_water_adjustment_kg, "Unit": "kg/m3", "Remarks": "Based on moisture/absorption"},
        {"Parameter": "Final batch water", "Symbol": "Wf", "Value": mix.final_batch_water_kg, "Unit": "kg/m3", "Remarks": "Field batch"},
        {"Parameter": "Final batch cement", "Symbol": "Cf", "Value": mix.final_batch_cement_kg, "Unit": "kg/m3", "Remarks": "Field batch"},
        {"Parameter": "Final batch fine aggregate", "Symbol": "FAf", "Value": mix.final_batch_fine_agg_kg, "Unit": "kg/m3", "Remarks": "Field batch"},
        {"Parameter": "Final batch coarse aggregate", "Symbol": "CAf", "Value": mix.final_batch_coarse_agg_kg, "Unit": "kg/m3", "Remarks": "Field batch"},
        {"Parameter": "Mix proportion", "Symbol": "-", "Value": mix.mix_proportion_by_weight, "Unit": "by weight", "Remarks": "C:FA:CA with w/c"},
        {"Parameter": "Assumptions", "Symbol": "-", "Value": mix.assumptions, "Unit": "-", "Remarks": mix.remarks},
    ]


def export_csv(mix: MixDesign) -> bytes:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=["Parameter", "Symbol", "Value", "Unit", "Remarks"])
    writer.writeheader()
    for row in mix_table_rows(mix):
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


def export_xlsx(mix: MixDesign) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = f"{mix.mix_id} Table"
    ws.append(["Parameter", "Symbol", "Value", "Unit", "Remarks"])
    for row in mix_table_rows(mix):
        ws.append([row["Parameter"], row["Symbol"], row["Value"], row["Unit"], row["Remarks"]])

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def export_pdf(mix: MixDesign) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 40
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, f"Concrete Mix Design Table - {mix.mix_id} ({mix.mix_name})")
    y -= 24

    c.setFont("Helvetica", 9)
    for row in mix_table_rows(mix):
        line = f"{row['Parameter']}: {row['Value']} {row['Unit']} ({row['Remarks']})"
        c.drawString(40, y, line[:120])
        y -= 14
        if y < 60:
            c.showPage()
            c.setFont("Helvetica", 9)
            y = height - 40

    c.save()
    return buffer.getvalue()
