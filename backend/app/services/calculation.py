import json
from dataclasses import asdict, dataclass

from app.models.mix import MixDesign


@dataclass
class RecalcOutcome:
    warnings: list[str]


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _update_proportion(mix: MixDesign) -> None:
    cement = mix.cement_content_kg_m3 or 1
    fine = mix.fine_agg_content_kg_m3 / cement
    coarse = mix.coarse_agg_content_kg_m3 / cement
    water = mix.water_content_kg_m3 / cement
    mix.mix_proportion_by_weight = f"1:{fine:.2f}:{coarse:.2f} (w/c={water:.2f})"


def recalculate_mix(mix: MixDesign, parameter: str, new_value: float) -> RecalcOutcome:
    warnings: list[str] = []

    if parameter == "water_cement_ratio":
        mix.water_cement_ratio = _clamp(new_value, 0.25, 0.70)
        mix.cement_content_kg_m3 = round(mix.water_content_kg_m3 / mix.water_cement_ratio, 2)
    elif parameter == "slump_mm":
        prev_slump = mix.slump_mm
        mix.slump_mm = _clamp(new_value, 20, 180)
        delta = (mix.slump_mm - prev_slump) / 10.0
        mix.water_content_kg_m3 = round(mix.water_content_kg_m3 + delta * 2.0, 2)
        mix.cement_content_kg_m3 = round(mix.water_content_kg_m3 / mix.water_cement_ratio, 2)
    elif parameter == "admixture_dosage_pct":
        mix.admixture_dosage_pct = _clamp(new_value, 0.0, 3.0)
        reduction = 1.0 - (mix.admixture_dosage_pct * 0.04)
        reduction = _clamp(reduction, 0.80, 1.0)
        mix.water_content_kg_m3 = round(mix.water_content_kg_m3 * reduction, 2)
        mix.cement_content_kg_m3 = round(mix.water_content_kg_m3 / mix.water_cement_ratio, 2)
    elif parameter == "moisture_correction_fine_pct":
        mix.moisture_correction_fine_pct = _clamp(new_value, -5.0, 8.0)
    elif parameter == "moisture_correction_coarse_pct":
        mix.moisture_correction_coarse_pct = _clamp(new_value, -5.0, 8.0)
    else:
        warnings.append(f"Unsupported recalculation parameter: {parameter}")

    # Field adjustment based on moisture/absorption.
    fine_adj = (mix.moisture_correction_fine_pct - mix.absorption_fine_pct) / 100.0 * mix.fine_agg_content_kg_m3
    coarse_adj = (mix.moisture_correction_coarse_pct - mix.absorption_coarse_pct) / 100.0 * mix.coarse_agg_content_kg_m3
    mix.field_water_adjustment_kg = round(-(fine_adj + coarse_adj), 2)

    mix.final_batch_water_kg = round(mix.water_content_kg_m3 + mix.field_water_adjustment_kg, 2)
    mix.final_batch_cement_kg = round(mix.cement_content_kg_m3, 2)
    mix.final_batch_fine_agg_kg = round(mix.fine_agg_content_kg_m3 * (1 + mix.moisture_correction_fine_pct / 100.0), 2)
    mix.final_batch_coarse_agg_kg = round(mix.coarse_agg_content_kg_m3 * (1 + mix.moisture_correction_coarse_pct / 100.0), 2)

    if not (0.3 <= mix.water_cement_ratio <= 0.65):
        warnings.append("Water-cement ratio is outside typical durable concrete range (0.30-0.65).")
    if mix.cement_content_kg_m3 < 280:
        warnings.append("Cement content is low; check minimum cement content requirement for exposure condition.")
    if mix.slump_mm > 150:
        warnings.append("High slump detected; verify segregation and bleeding risk.")

    _update_proportion(mix)
    return RecalcOutcome(warnings=warnings)


def mix_snapshot(mix: MixDesign) -> str:
    payload = {
        "mix_id": mix.mix_id,
        "w_c_ratio": mix.water_cement_ratio,
        "water": mix.water_content_kg_m3,
        "cement": mix.cement_content_kg_m3,
        "fine": mix.fine_agg_content_kg_m3,
        "coarse": mix.coarse_agg_content_kg_m3,
        "slump": mix.slump_mm,
        "admixture_dose": mix.admixture_dosage_pct,
        "field_water_adjustment": mix.field_water_adjustment_kg,
    }
    return json.dumps(payload)
