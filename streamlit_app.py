import os
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Concrete Mix Design Manager", layout="wide")

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000/api")

st.title("Concrete Mix Design Manager")
st.caption("QR-enabled mix design library with exports and recalculation")

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
    df = pd.DataFrame(items)[[
        "mix_id", "mix_name", "concrete_grade", "design_method", "cement_type", "category", "status", "slug"
    ]]
    st.dataframe(df, use_container_width=True)
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
                ["Grade of concrete", mix["concrete_grade"], "-"],
                ["Target mean strength", mix["target_mean_strength"], "MPa"],
                ["Water-cement ratio", mix["water_cement_ratio"], "-"],
                ["Water content", mix["water_content_kg_m3"], "kg/m3"],
                ["Cement content", mix["cement_content_kg_m3"], "kg/m3"],
                ["Fine aggregate", mix["fine_agg_content_kg_m3"], "kg/m3"],
                ["Coarse aggregate", mix["coarse_agg_content_kg_m3"], "kg/m3"],
                ["Admixture dosage", mix["admixture_dosage_pct"], "%"],
                ["Water adjustment", mix["field_water_adjustment_kg"], "kg/m3"],
                ["Mix proportion", mix["mix_proportion_by_weight"], "by wt"],
            ]
            st.table(pd.DataFrame(table_rows, columns=["Parameter", "Value", "Unit"]))

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
