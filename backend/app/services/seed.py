from sqlalchemy.orm import Session

from app.models.mix import MixDesign, MixStatus
from app.models.support import Admixture, Material
from app.services.qr import generate_qr_assets


def _grade_to_strength(grade: str) -> float:
    return float(grade.replace("M", ""))


def seed_mixes(db: Session, count: int = 60) -> int:
    # Enforce IS-only method for existing records too.
    db.query(MixDesign).filter(MixDesign.design_method != "IS 10262:2019").update(
        {"design_method": "IS 10262:2019"}, synchronize_session=False
    )
    if db.query(Material).count() == 0:
        db.add_all(
            [
                Material(material_code="CEM-OPC53", name="OPC 53 Cement", specific_gravity=3.15),
                Material(material_code="FA-RIVER", name="Fine Aggregate (River Sand)", specific_gravity=2.65),
                Material(material_code="CA-20MM", name="Coarse Aggregate 20mm", specific_gravity=2.70),
            ]
        )
    if db.query(Admixture).count() == 0:
        db.add_all(
            [
                Admixture(admixture_code="ADM-PCE", name="PCE Superplasticizer", default_dosage_pct=0.8),
                Admixture(admixture_code="ADM-SNF", name="SNF Superplasticizer", default_dosage_pct=0.6),
            ]
        )

    existing = db.query(MixDesign).count()
    if existing > 0:
        db.commit()
        return existing

    grades = ["M20", "M25", "M30", "M35", "M40", "M45", "M50"]
    cements = ["OPC 43", "OPC 53", "PPC", "PSC"]
    exposures = ["Mild", "Moderate", "Severe", "Very Severe"]
    categories = ["pavement mix", "structural mix", "nominal mix", "design mix", "trial mix", "site-adjusted mix"]
    admixtures = ["None", "SNF Superplasticizer", "PCE Superplasticizer", "Retarder"]

    for i in range(1, count + 1):
        grade = grades[i % len(grades)]
        fck = _grade_to_strength(grade)
        w_c = round(0.56 - (fck - 20) * 0.006, 3)
        w_c = max(0.32, min(0.58, w_c))
        water = round(185 - (i % 5) * 3 + (i % 3) * 1.5, 2)
        cement = round(water / w_c, 2)
        fine = round(650 + (i % 6) * 18, 2)
        coarse = round(1120 + (i % 7) * 22, 2)

        mix = MixDesign(
            mix_id=f"MX-{i:04d}",
            slug=f"mix-{i:04d}",
            mix_name=f"{grade} Mix Variant {i}",
            project_tag=f"Project-{(i % 10) + 1}",
            concrete_grade=grade,
            target_mean_strength=round(fck + 8.0, 2),
            design_method="IS 10262:2019",
            cement_type=cements[i % len(cements)],
            max_aggregate_size_mm=20 if i % 2 == 0 else 10,
            exposure_condition=exposures[i % len(exposures)],
            slump_mm=75 + (i % 4) * 25,
            water_cement_ratio=w_c,
            water_content_kg_m3=water,
            cement_content_kg_m3=cement,
            fine_agg_content_kg_m3=fine,
            coarse_agg_content_kg_m3=coarse,
            admixture_type=admixtures[i % len(admixtures)],
            admixture_dosage_pct=0.0 if i % 4 == 0 else round(0.6 + (i % 3) * 0.2, 2),
            moisture_correction_fine_pct=round((i % 4) * 0.5, 2),
            moisture_correction_coarse_pct=round((i % 3) * 0.3, 2),
            absorption_fine_pct=0.8,
            absorption_coarse_pct=0.6,
            field_water_adjustment_kg=0.0,
            final_batch_water_kg=water,
            final_batch_cement_kg=cement,
            final_batch_fine_agg_kg=fine,
            final_batch_coarse_agg_kg=coarse,
            mix_proportion_by_weight=f"1:{fine / cement:.2f}:{coarse / cement:.2f} (w/c={w_c:.2f})",
            assumptions="Standard SSD aggregates and ambient 27C.",
            remarks="Seeded demo mix for ready-reference database.",
            category=categories[i % len(categories)],
            status=MixStatus.approved if i % 3 == 0 else MixStatus.draft,
            is_public=True if i % 5 == 0 else False,
            download_ref=f"/api/mixes/mix-{i:04d}/export/pdf",
        )

        png, svg = generate_qr_assets(mix.slug)
        mix.qr_path_png = png
        mix.qr_path_svg = svg

        db.add(mix)

    db.commit()
    return count
