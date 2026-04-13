from datetime import datetime
from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.database import Base


class MixStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    trial = "trial"
    archived = "archived"


class MixDesign(Base):
    __tablename__ = "mix_designs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    mix_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    mix_name: Mapped[str] = mapped_column(String(140), index=True)
    project_tag: Mapped[str] = mapped_column(String(80), default="general")

    concrete_grade: Mapped[str] = mapped_column(String(10), index=True)
    target_mean_strength: Mapped[float] = mapped_column(Float)
    design_method: Mapped[str] = mapped_column(String(60), index=True)
    cement_type: Mapped[str] = mapped_column(String(80), index=True)
    max_aggregate_size_mm: Mapped[float] = mapped_column(Float, index=True)
    exposure_condition: Mapped[str] = mapped_column(String(80), index=True)
    slump_mm: Mapped[float] = mapped_column(Float, index=True)

    water_cement_ratio: Mapped[float] = mapped_column(Float)
    water_content_kg_m3: Mapped[float] = mapped_column(Float)
    cement_content_kg_m3: Mapped[float] = mapped_column(Float)
    fine_agg_content_kg_m3: Mapped[float] = mapped_column(Float)
    coarse_agg_content_kg_m3: Mapped[float] = mapped_column(Float)

    admixture_type: Mapped[str] = mapped_column(String(100), default="None", index=True)
    admixture_dosage_pct: Mapped[float] = mapped_column(Float, default=0.0)

    sg_cement: Mapped[float] = mapped_column(Float, default=3.15)
    sg_fine_agg: Mapped[float] = mapped_column(Float, default=2.65)
    sg_coarse_agg: Mapped[float] = mapped_column(Float, default=2.70)
    sg_admixture: Mapped[float] = mapped_column(Float, default=1.10)

    moisture_correction_fine_pct: Mapped[float] = mapped_column(Float, default=0.0)
    moisture_correction_coarse_pct: Mapped[float] = mapped_column(Float, default=0.0)
    absorption_fine_pct: Mapped[float] = mapped_column(Float, default=0.0)
    absorption_coarse_pct: Mapped[float] = mapped_column(Float, default=0.0)

    field_water_adjustment_kg: Mapped[float] = mapped_column(Float, default=0.0)
    final_batch_water_kg: Mapped[float] = mapped_column(Float)
    final_batch_cement_kg: Mapped[float] = mapped_column(Float)
    final_batch_fine_agg_kg: Mapped[float] = mapped_column(Float)
    final_batch_coarse_agg_kg: Mapped[float] = mapped_column(Float)
    mix_proportion_by_weight: Mapped[str] = mapped_column(String(120))

    quantity_basis: Mapped[str] = mapped_column(String(120), default="Per 1 m3")
    assumptions: Mapped[str] = mapped_column(Text, default="")
    remarks: Mapped[str] = mapped_column(Text, default="")

    category: Mapped[str] = mapped_column(String(40), default="design mix", index=True)
    status: Mapped[MixStatus] = mapped_column(Enum(MixStatus), default=MixStatus.draft, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    qr_path_png: Mapped[str] = mapped_column(String(255), default="")
    qr_path_svg: Mapped[str] = mapped_column(String(255), default="")
    download_ref: Mapped[str] = mapped_column(String(255), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    revisions: Mapped[list["MixRevision"]] = relationship(back_populates="mix", cascade="all, delete-orphan")


class MixRevision(Base):
    __tablename__ = "mix_revisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mix_design_id: Mapped[int] = mapped_column(ForeignKey("mix_designs.id"), index=True)
    revision_label: Mapped[str] = mapped_column(String(40))
    changed_parameter: Mapped[str] = mapped_column(String(60))
    old_value: Mapped[str] = mapped_column(String(80))
    new_value: Mapped[str] = mapped_column(String(80))
    warning_message: Mapped[str] = mapped_column(Text, default="")
    snapshot_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    mix: Mapped[MixDesign] = relationship(back_populates="revisions")
