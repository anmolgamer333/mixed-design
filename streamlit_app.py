import os
import sys
import time
from pathlib import Path
import threading

import requests
import streamlit as st

st.set_page_config(page_title="Concrete Mix Design Manager", layout="wide")

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8001/api")
AUTO_START_BACKEND = os.getenv("AUTO_START_BACKEND", "1") != "0"
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8001"))


def api_available(timeout: int = 2) -> bool:
    try:
        r = requests.get(f"{API_BASE}/mixes", params={"page_size": 1}, timeout=timeout)
        r.raise_for_status()
        return True
    except requests.RequestException:
        return False


@st.cache_resource(show_spinner=False)
def ensure_backend_started():
    if api_available():
        return None

    if not AUTO_START_BACKEND:
        return None

    root = Path(__file__).resolve().parent
    backend_dir = root / "backend"
    os.environ.setdefault("DATABASE_URL", "sqlite:///./mix_designs.db")
    os.environ.setdefault("BASE_PUBLIC_URL", "http://localhost:8501")

    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    def run_backend() -> None:
        import uvicorn
        from app.main import app

        uvicorn.run(app, host="127.0.0.1", port=BACKEND_PORT, log_level="warning")

    thread = threading.Thread(target=run_backend, daemon=True)
    thread.start()

    for _ in range(30):
        if api_available(timeout=1):
            return "embedded-backend"
        time.sleep(1)

    return "embedded-backend-timeout"


st.title("Concrete Mix Design Manager")
st.caption("QR-enabled mix design library with exports and recalculation")

ensure_backend_started()
if not api_available():
    st.error("Mix Design backend is not reachable.")
    st.code(
        "cd backend\n"
        "$env:DATABASE_URL='sqlite:///./mix_designs.db'\n"
        "$env:BASE_PUBLIC_URL='http://localhost:8501'\n"
        "python -m uvicorn app.main:app --host 127.0.0.1 --port 8001"
    )
    st.stop()

with st.sidebar:
    st.header("Filters")
    q = st.text_input("Search")
    grade = st.selectbox("Grade", ["", "M20", "M25", "M30", "M35", "M40", "M45", "M50"])
    sort_by = st.selectbox("Sort", ["recent", "alphabetical", "grade", "mix_id"])
    page_size = st.slider("Page Size", 10, 100, 30)

params = {
    "q": q or None,
    "grade": grade or None,
    "sort_by": sort_by,
    "page": 1,
    "page_size": page_size,
}

resp = requests.get(f"{API_BASE}/mixes", params=params, timeout=20)
resp.raise_for_status()
data = resp.json()
items = data.get("items", [])

col1, col2, col3, col4 = st.columns(4)
try:
    summary = requests.get(f"{API_BASE}/mixes/dashboard/summary", timeout=20).json()
    col1.metric("Total Mixes", summary.get("total_mixes", 0))
    col2.metric("Approved", summary.get("approved", 0))
    col3.metric("Trial", summary.get("trial", 0))
    col4.metric("Archived", summary.get("archived", 0))
except Exception:
    col1.metric("Total Mixes", data.get("total", 0))

st.subheader("Mix Database")
if items:
    rows = []
    for m in items:
        rows.append(
            {
                "mix_id": m.get("mix_id"),
                "mix_name": m.get("mix_name"),
                "concrete_grade": m.get("concrete_grade"),
                "design_method": m.get("design_method"),
                "cement_type": m.get("cement_type"),
                "category": m.get("category"),
                "status": m.get("status"),
                "slug": m.get("slug"),
            }
        )
    st.dataframe(rows, use_container_width=True)
else:
    st.info("No records found.")

slug = st.text_input("Open mix by slug", value=(items[0]["slug"] if items else ""))
if slug:
    detail = requests.get(f"{API_BASE}/mixes/{slug}", timeout=20)
    if detail.status_code == 200:
        mix = detail.json()
        st.subheader(f"{mix['mix_name']} ({mix['mix_id']})")

        c1, c2 = st.columns([2, 1])
        with c1:
            table_rows = [
                {"Parameter": "Grade of concrete", "Value": mix["concrete_grade"], "Unit": "-"},
                {"Parameter": "Target mean strength", "Value": mix["target_mean_strength"], "Unit": "MPa"},
                {"Parameter": "Water-cement ratio", "Value": mix["water_cement_ratio"], "Unit": "-"},
                {"Parameter": "Water content", "Value": mix["water_content_kg_m3"], "Unit": "kg/m3"},
                {"Parameter": "Cement content", "Value": mix["cement_content_kg_m3"], "Unit": "kg/m3"},
                {"Parameter": "Fine aggregate", "Value": mix["fine_agg_content_kg_m3"], "Unit": "kg/m3"},
                {"Parameter": "Coarse aggregate", "Value": mix["coarse_agg_content_kg_m3"], "Unit": "kg/m3"},
                {"Parameter": "Admixture dosage", "Value": mix["admixture_dosage_pct"], "Unit": "%"},
                {"Parameter": "Water adjustment", "Value": mix["field_water_adjustment_kg"], "Unit": "kg/m3"},
                {"Parameter": "Mix proportion", "Value": mix["mix_proportion_by_weight"], "Unit": "by wt"},
            ]
            st.table(table_rows)

            st.markdown("### Recalculate")
            parameter = st.selectbox(
                "Parameter",
                [
                    "water_cement_ratio",
                    "slump_mm",
                    "admixture_dosage_pct",
                    "moisture_correction_fine_pct",
                    "moisture_correction_coarse_pct",
                ],
            )
            new_value = st.number_input("New value", value=float(mix.get(parameter, 0) or 0), format="%.3f")
            if st.button("Recalculate and Save Revision"):
                r = requests.post(
                    f"{API_BASE}/mixes/{slug}/recalculate",
                    json={"parameter": parameter, "new_value": float(new_value), "save_revision": True},
                    timeout=20,
                )
                if r.status_code == 200:
                    out = r.json()
                    warns = out.get("warnings", [])
                    if warns:
                        for w in warns:
                            st.warning(w)
                    st.success("Recalculation completed.")
                    st.rerun()
                else:
                    st.error(r.text)

        with c2:
            st.markdown("### QR")
            st.image(f"{API_BASE}/mixes/{slug}/qr/png", caption=f"QR for {slug}")
            st.markdown(f"[Download CSV]({API_BASE}/mixes/{slug}/export/csv)")
            st.markdown(f"[Download Excel]({API_BASE}/mixes/{slug}/export/xlsx)")
            st.markdown(f"[Download PDF]({API_BASE}/mixes/{slug}/export/pdf)")
            st.markdown(f"[Download QR PNG]({API_BASE}/mixes/{slug}/qr/png)")
            st.markdown(f"[Download QR SVG]({API_BASE}/mixes/{slug}/qr/svg)")
    else:
        st.error("Mix not found")

st.markdown("---")
st.markdown("### Bulk Import")
upload = st.file_uploader("Upload CSV or XLSX", type=["csv", "xlsx"])
if upload and st.button("Run Import"):
    files = {"file": (upload.name, upload.getvalue(), upload.type)}
    r = requests.post(f"{API_BASE}/mixes/import", files=files, timeout=60)
    if r.status_code == 200:
        out = r.json()
        st.success(f"Imported {out['imported']} of {out['total_rows']} rows")
    else:
        st.error(r.text)

st.markdown(f"[Download QR Sheet PDF]({API_BASE}/mixes/qr/sheet?limit=60)")
st.markdown(f"[Export Full Database JSON]({API_BASE}/mixes/database/export)")
