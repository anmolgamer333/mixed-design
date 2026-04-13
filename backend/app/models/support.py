from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    specific_gravity: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20), default="kg")
    notes: Mapped[str] = mapped_column(Text, default="")


class Admixture(Base):
    __tablename__ = "admixtures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admixture_code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    default_dosage_pct: Mapped[float] = mapped_column(Float, default=0.8)
    effect_notes: Mapped[str] = mapped_column(Text, default="")


class QrCode(Base):
    __tablename__ = "qr_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mix_design_id: Mapped[int] = mapped_column(ForeignKey("mix_designs.id"), index=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    png_path: Mapped[str] = mapped_column(String(255))
    svg_path: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(40), default="admin")
    password_hash: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ExportLog(Base):
    __tablename__ = "export_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mix_design_id: Mapped[int] = mapped_column(ForeignKey("mix_designs.id"), index=True)
    export_format: Mapped[str] = mapped_column(String(20))
    exported_by: Mapped[str] = mapped_column(String(60), default="system")
    exported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
