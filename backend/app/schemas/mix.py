from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.mix import MixStatus

IS_METHOD = "IS 10262:2019"


class MixDesignBase(BaseModel):
    mix_id: str
    slug: str
    mix_name: str
    project_tag: str = "general"
    concrete_grade: str
    target_mean_strength: float
    design_method: str
    cement_type: str
    max_aggregate_size_mm: float
    exposure_condition: str
    slump_mm: float
    water_cement_ratio: float = Field(..., ge=0.2, le=0.8)
    water_content_kg_m3: float
    cement_content_kg_m3: float
    fine_agg_content_kg_m3: float
    coarse_agg_content_kg_m3: float
    admixture_type: str = "None"
    admixture_dosage_pct: float = 0.0
    sg_cement: float = 3.15
    sg_fine_agg: float = 2.65
    sg_coarse_agg: float = 2.70
    sg_admixture: float = 1.10
    moisture_correction_fine_pct: float = 0.0
    moisture_correction_coarse_pct: float = 0.0
    absorption_fine_pct: float = 0.0
    absorption_coarse_pct: float = 0.0
    field_water_adjustment_kg: float = 0.0
    final_batch_water_kg: float
    final_batch_cement_kg: float
    final_batch_fine_agg_kg: float
    final_batch_coarse_agg_kg: float
    mix_proportion_by_weight: str
    quantity_basis: str = "Per 1 m3"
    assumptions: str = ""
    remarks: str = ""
    category: str = "design mix"
    status: MixStatus = MixStatus.draft
    is_public: bool = False

    @field_validator("design_method")
    @classmethod
    def validate_design_method(cls, v: str) -> str:
        if v != IS_METHOD:
            raise ValueError(f"Only {IS_METHOD} is supported")
        return v


class MixDesignCreate(MixDesignBase):
    pass


class MixDesignUpdate(BaseModel):
    mix_name: Optional[str] = None
    project_tag: Optional[str] = None
    concrete_grade: Optional[str] = None
    target_mean_strength: Optional[float] = None
    design_method: Optional[str] = None
    cement_type: Optional[str] = None
    max_aggregate_size_mm: Optional[float] = None
    exposure_condition: Optional[str] = None
    slump_mm: Optional[float] = None
    water_cement_ratio: Optional[float] = None
    water_content_kg_m3: Optional[float] = None
    cement_content_kg_m3: Optional[float] = None
    fine_agg_content_kg_m3: Optional[float] = None
    coarse_agg_content_kg_m3: Optional[float] = None
    admixture_type: Optional[str] = None
    admixture_dosage_pct: Optional[float] = None
    sg_cement: Optional[float] = None
    sg_fine_agg: Optional[float] = None
    sg_coarse_agg: Optional[float] = None
    sg_admixture: Optional[float] = None
    moisture_correction_fine_pct: Optional[float] = None
    moisture_correction_coarse_pct: Optional[float] = None
    absorption_fine_pct: Optional[float] = None
    absorption_coarse_pct: Optional[float] = None
    field_water_adjustment_kg: Optional[float] = None
    final_batch_water_kg: Optional[float] = None
    final_batch_cement_kg: Optional[float] = None
    final_batch_fine_agg_kg: Optional[float] = None
    final_batch_coarse_agg_kg: Optional[float] = None
    mix_proportion_by_weight: Optional[str] = None
    quantity_basis: Optional[str] = None
    assumptions: Optional[str] = None
    remarks: Optional[str] = None
    category: Optional[str] = None
    status: Optional[MixStatus] = None
    is_public: Optional[bool] = None

    @field_validator("design_method")
    @classmethod
    def validate_design_method(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v != IS_METHOD:
            raise ValueError(f"Only {IS_METHOD} is supported")
        return v


class MixDesignOut(MixDesignBase):
    id: int
    created_at: datetime
    updated_at: datetime
    qr_path_png: str
    qr_path_svg: str
    download_ref: str

    class Config:
        from_attributes = True


class MixListResponse(BaseModel):
    total: int
    items: list[MixDesignOut]


class RecalculateRequest(BaseModel):
    parameter: str
    new_value: float
    save_revision: bool = True


class RecalculateResponse(BaseModel):
    updated_mix: MixDesignOut
    warnings: list[str]


class RevisionOut(BaseModel):
    id: int
    mix_design_id: int
    revision_label: str
    changed_parameter: str
    old_value: str
    new_value: str
    warning_message: str
    snapshot_json: str
    created_at: datetime

    class Config:
        from_attributes = True
