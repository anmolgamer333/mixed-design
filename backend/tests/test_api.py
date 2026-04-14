from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.mixes import router
from app.db.database import Base, get_db
from app.models.mix import MixDesign
from app.services.qr import generate_qr_assets


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_mix.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def build_test_app():
    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_db] = override_get_db
    return app


def seed_one(db):
    if db.query(MixDesign).count() > 0:
        return
    mix = MixDesign(
        mix_id="MX-T001",
        slug="mx-t001",
        mix_name="Test Mix",
        project_tag="Test",
        concrete_grade="M30",
        target_mean_strength=38,
        design_method="IS 10262:2019",
        cement_type="OPC 53",
        max_aggregate_size_mm=20,
        exposure_condition="Moderate",
        slump_mm=100,
        water_cement_ratio=0.45,
        water_content_kg_m3=180,
        cement_content_kg_m3=400,
        fine_agg_content_kg_m3=680,
        coarse_agg_content_kg_m3=1150,
        admixture_type="PCE",
        admixture_dosage_pct=0.8,
        final_batch_water_kg=180,
        final_batch_cement_kg=400,
        final_batch_fine_agg_kg=680,
        final_batch_coarse_agg_kg=1150,
        mix_proportion_by_weight="1:1.7:2.8 (w/c=0.45)",
    )
    png, svg = generate_qr_assets(mix.slug)
    mix.qr_path_png = png
    mix.qr_path_svg = svg
    mix.download_ref = "/api/mixes/mx-t001/export/pdf"
    db.add(mix)
    db.commit()


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        seed_one(db)
    finally:
        db.close()


def teardown_module():
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if Path("test_mix.db").exists():
        try:
            Path("test_mix.db").unlink()
        except PermissionError:
            pass


def test_crud_and_list():
    app = build_test_app()
    client = TestClient(app)

    resp = client.get("/api/mixes")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1

    payload = {
        "mix_id": "MX-T002",
        "slug": "mx-t002",
        "mix_name": "Created Mix",
        "project_tag": "Lab",
        "concrete_grade": "M35",
        "target_mean_strength": 43,
        "design_method": "IS 10262:2019",
        "cement_type": "OPC 53",
        "max_aggregate_size_mm": 20,
        "exposure_condition": "Severe",
        "slump_mm": 120,
        "water_cement_ratio": 0.42,
        "water_content_kg_m3": 176,
        "cement_content_kg_m3": 419,
        "fine_agg_content_kg_m3": 700,
        "coarse_agg_content_kg_m3": 1120,
        "admixture_type": "PCE",
        "admixture_dosage_pct": 1.0,
        "final_batch_water_kg": 176,
        "final_batch_cement_kg": 419,
        "final_batch_fine_agg_kg": 700,
        "final_batch_coarse_agg_kg": 1120,
        "mix_proportion_by_weight": "1:1.67:2.67 (w/c=0.42)",
    }

    create = client.post("/api/mixes", json=payload)
    assert create.status_code == 200

    get_one = client.get("/api/mixes/mx-t002")
    assert get_one.status_code == 200

    delete = client.delete("/api/mixes/mx-t002")
    assert delete.status_code == 200


def test_qr_and_exports():
    app = build_test_app()
    client = TestClient(app)

    qr = client.get("/api/mixes/mx-t001/qr/png")
    assert qr.status_code == 200
    assert qr.headers["content-type"].startswith("image/png")

    csv_resp = client.get("/api/mixes/mx-t001/export/csv")
    assert csv_resp.status_code == 200
    assert "Parameter" in csv_resp.text

    xlsx_resp = client.get("/api/mixes/mx-t001/export/xlsx")
    assert xlsx_resp.status_code == 200
    assert xlsx_resp.headers["content-type"].startswith("application/vnd.openxmlformats")

    pdf_resp = client.get("/api/mixes/mx-t001/export/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"].startswith("application/pdf")


def test_recalculation_creates_revision():
    app = build_test_app()
    client = TestClient(app)

    recalc = client.post("/api/mixes/mx-t001/recalculate", json={"parameter": "water_cement_ratio", "new_value": 0.4, "save_revision": True})
    assert recalc.status_code == 200
    body = recalc.json()
    assert body["updated_mix"]["water_cement_ratio"] == 0.4

    revisions = client.get("/api/mixes/mx-t001/revisions")
    assert revisions.status_code == 200
    assert len(revisions.json()) >= 1
