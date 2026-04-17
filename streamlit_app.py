import os
import sys
import time
from pathlib import Path
import threading

import requests
import streamlit as st

st.set_page_config(page_title="Concrete Mix Design Manager", layout="wide")

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8001/api").rstrip("/")
AUTO_START_BACKEND = os.getenv("AUTO_START_BACKEND", "1") != "0"
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8001"))
_backend_thread_started = False
_backend_error_message = ""
HTTP = requests.Session()
HTTP.trust_env = False


def infer_public_base_url() -> str | None:
    try:
        headers = dict(st.context.headers)
        host = headers.get("host") or headers.get("Host")
        proto = headers.get("x-forwarded-proto") or headers.get("X-Forwarded-Proto") or "https"
        if host:
            return f"{proto}://{host}"
    except Exception:
        return None
    return None


INFERRED_PUBLIC_BASE_URL = infer_public_base_url()
QR_PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", INFERRED_PUBLIC_BASE_URL or "").rstrip("/")


def _api_url(path: str) -> str:
    if not path.startswith("/"):
        path = "/" + path
    return f"{API_BASE}{path}"


def api_get(path: str, **kwargs):
    return HTTP.get(_api_url(path), **kwargs)


def api_post(path: str, **kwargs):
    return HTTP.post(_api_url(path), **kwargs)


def api_put(path: str, **kwargs):
    return HTTP.put(_api_url(path), **kwargs)


def api_available(timeout: int = 2) -> bool:
    try:
        r = api_get("/mixes", params={"page_size": 1}, timeout=timeout)
        r.raise_for_status()
        return True
    except requests.RequestException:
        return False


def ensure_backend_started():
    global _backend_thread_started
    global _backend_error_message

    if api_available():
        _backend_error_message = ""
        return None

    if not AUTO_START_BACKEND:
        return None

    if _backend_thread_started:
        # Backend thread already launched; give it time to come up.
        for _ in range(15):
            if api_available(timeout=1):
                return "embedded-backend"
            time.sleep(1)
        return "embedded-backend-timeout"

    root = Path(__file__).resolve().parent
    backend_dir = root / "backend"
    os.environ.setdefault("DATABASE_URL", "sqlite:///./mix_designs.db")
    os.environ.setdefault("BASE_PUBLIC_URL", INFERRED_PUBLIC_BASE_URL or "http://localhost:8501")

    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    try:
        import uvicorn  # noqa: F401
        from app.main import app  # noqa: F401
    except Exception as exc:
        _backend_error_message = f"{type(exc).__name__}: {exc}"
        return "backend-import-failed"

    def run_backend() -> None:
        global _backend_error_message
        import uvicorn
        try:
            from app.main import app
            uvicorn.run(app, host="127.0.0.1", port=BACKEND_PORT, log_level="warning")
        except Exception as exc:
            _backend_error_message = f"{type(exc).__name__}: {exc}"

    thread = threading.Thread(target=run_backend, daemon=True)
    thread.start()
    _backend_thread_started = True

    for _ in range(45):
        if api_available(timeout=1):
            return "embedded-backend"
        time.sleep(1)

    return "embedded-backend-timeout"


st.title("Concrete Mix Design Manager")
st.caption("QR-enabled mix design library with exports and recalculation")

ensure_backend_started()
if not api_available():
    st.error("Mix Design backend is not reachable.")
    st.info(f"Using API base URL: {API_BASE}")
    if _backend_error_message:
        st.warning(f"Backend startup error: {_backend_error_message}")
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

resp = api_get("/mixes", params=params, timeout=20)
resp.raise_for_status()
data = resp.json()
items = data.get("items", [])

col1, col2, col3, col4 = st.columns(4)
try:
    summary = api_get("/mixes/dashboard/summary", timeout=20).json()
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
    st.dataframe(rows, width="stretch")
else:
    st.info("No records found.")

query_slug = st.query_params.get("slug", "")
if isinstance(query_slug, list):
    query_slug = query_slug[0] if query_slug else ""
default_slug = query_slug or (items[0]["slug"] if items else "")
slug = st.text_input("Open mix by slug", value=default_slug)
if slug and st.query_params.get("slug") != slug:
    st.query_params["slug"] = slug


def render_download_button(
    label: str,
    path: str,
    filename: str,
    mime: str,
    params: dict | None = None,
    timeout: int = 30,
) -> None:
    try:
        resp = api_get(path, timeout=timeout, params=params)
        if resp.status_code == 200:
            st.download_button(label, data=resp.content, file_name=filename, mime=mime, use_container_width=True)
        else:
            st.caption(f"{label} unavailable")
    except requests.RequestException:
        st.caption(f"{label} unavailable")


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def local_recalc_preview(mix_data: dict, parameter: str, new_value: float) -> tuple[dict, list[str]]:
    m = dict(mix_data)
    warnings: list[str] = []

    if parameter == "water_cement_ratio":
        m["water_cement_ratio"] = _clamp(float(new_value), 0.25, 0.70)
        m["cement_content_kg_m3"] = round(float(m["water_content_kg_m3"]) / float(m["water_cement_ratio"]), 2)
    elif parameter == "slump_mm":
        prev_slump = float(m["slump_mm"])
        m["slump_mm"] = _clamp(float(new_value), 20.0, 180.0)
        delta = (float(m["slump_mm"]) - prev_slump) / 10.0
        m["water_content_kg_m3"] = round(float(m["water_content_kg_m3"]) + delta * 2.0, 2)
        m["cement_content_kg_m3"] = round(float(m["water_content_kg_m3"]) / float(m["water_cement_ratio"]), 2)
    elif parameter == "admixture_dosage_pct":
        m["admixture_dosage_pct"] = _clamp(float(new_value), 0.0, 3.0)
        reduction = 1.0 - (float(m["admixture_dosage_pct"]) * 0.04)
        reduction = _clamp(reduction, 0.80, 1.0)
        m["water_content_kg_m3"] = round(float(m["water_content_kg_m3"]) * reduction, 2)
        m["cement_content_kg_m3"] = round(float(m["water_content_kg_m3"]) / float(m["water_cement_ratio"]), 2)
    elif parameter == "moisture_correction_fine_pct":
        m["moisture_correction_fine_pct"] = _clamp(float(new_value), -5.0, 8.0)
    elif parameter == "moisture_correction_coarse_pct":
        m["moisture_correction_coarse_pct"] = _clamp(float(new_value), -5.0, 8.0)
    else:
        warnings.append(f"Unsupported recalculation parameter: {parameter}")

    fine_adj = (
        (float(m.get("moisture_correction_fine_pct", 0.0)) - float(m.get("absorption_fine_pct", 0.0)))
        / 100.0
        * float(m.get("fine_agg_content_kg_m3", 0.0))
    )
    coarse_adj = (
        (float(m.get("moisture_correction_coarse_pct", 0.0)) - float(m.get("absorption_coarse_pct", 0.0)))
        / 100.0
        * float(m.get("coarse_agg_content_kg_m3", 0.0))
    )
    m["field_water_adjustment_kg"] = round(-(fine_adj + coarse_adj), 2)

    m["final_batch_water_kg"] = round(float(m["water_content_kg_m3"]) + float(m["field_water_adjustment_kg"]), 2)
    m["final_batch_cement_kg"] = round(float(m["cement_content_kg_m3"]), 2)
    m["final_batch_fine_agg_kg"] = round(
        float(m["fine_agg_content_kg_m3"]) * (1 + float(m.get("moisture_correction_fine_pct", 0.0)) / 100.0), 2
    )
    m["final_batch_coarse_agg_kg"] = round(
        float(m["coarse_agg_content_kg_m3"]) * (1 + float(m.get("moisture_correction_coarse_pct", 0.0)) / 100.0), 2
    )

    if not (0.3 <= float(m["water_cement_ratio"]) <= 0.65):
        warnings.append("Water-cement ratio is outside typical durable concrete range (0.30-0.65).")
    if float(m["cement_content_kg_m3"]) < 280:
        warnings.append("Cement content is low; check minimum cement content requirement for exposure condition.")
    if float(m["slump_mm"]) > 150:
        warnings.append("High slump detected; verify segregation and bleeding risk.")

    cement = float(m["cement_content_kg_m3"]) or 1.0
    fine = float(m["fine_agg_content_kg_m3"]) / cement
    coarse = float(m["coarse_agg_content_kg_m3"]) / cement
    water = float(m["water_content_kg_m3"]) / cement
    m["mix_proportion_by_weight"] = f"1:{fine:.2f}:{coarse:.2f} (w/c={water:.2f})"
    return m, warnings


UPDATE_FIELDS = [
    "mix_name",
    "project_tag",
    "concrete_grade",
    "target_mean_strength",
    "design_method",
    "cement_type",
    "max_aggregate_size_mm",
    "exposure_condition",
    "slump_mm",
    "water_cement_ratio",
    "water_content_kg_m3",
    "cement_content_kg_m3",
    "fine_agg_content_kg_m3",
    "coarse_agg_content_kg_m3",
    "admixture_type",
    "admixture_dosage_pct",
    "sg_cement",
    "sg_fine_agg",
    "sg_coarse_agg",
    "sg_admixture",
    "moisture_correction_fine_pct",
    "moisture_correction_coarse_pct",
    "absorption_fine_pct",
    "absorption_coarse_pct",
    "field_water_adjustment_kg",
    "final_batch_water_kg",
    "final_batch_cement_kg",
    "final_batch_fine_agg_kg",
    "final_batch_coarse_agg_kg",
    "mix_proportion_by_weight",
    "quantity_basis",
    "assumptions",
    "remarks",
    "category",
    "status",
    "is_public",
]


CREATE_FIELDS = [
    "mix_id",
    "slug",
    "mix_name",
    "project_tag",
    "concrete_grade",
    "target_mean_strength",
    "design_method",
    "cement_type",
    "max_aggregate_size_mm",
    "exposure_condition",
    "slump_mm",
    "water_cement_ratio",
    "water_content_kg_m3",
    "cement_content_kg_m3",
    "fine_agg_content_kg_m3",
    "coarse_agg_content_kg_m3",
    "admixture_type",
    "admixture_dosage_pct",
    "sg_cement",
    "sg_fine_agg",
    "sg_coarse_agg",
    "sg_admixture",
    "moisture_correction_fine_pct",
    "moisture_correction_coarse_pct",
    "absorption_fine_pct",
    "absorption_coarse_pct",
    "field_water_adjustment_kg",
    "final_batch_water_kg",
    "final_batch_cement_kg",
    "final_batch_fine_agg_kg",
    "final_batch_coarse_agg_kg",
    "mix_proportion_by_weight",
    "quantity_basis",
    "assumptions",
    "remarks",
    "category",
    "status",
    "is_public",
]


if slug:
    detail = api_get(f"/mixes/{slug}", timeout=20)
    if detail.status_code == 200:
        mix = detail.json()
        st.subheader(f"{mix['mix_name']} ({mix['mix_id']})")

        c1, c2 = st.columns([2, 1])
        with c1:
            table_rows = [
                {"Parameter": "Grade of concrete", "Value": str(mix["concrete_grade"]), "Unit": "-"},
                {"Parameter": "Target mean strength", "Value": str(mix["target_mean_strength"]), "Unit": "MPa"},
                {"Parameter": "Water-cement ratio", "Value": str(mix["water_cement_ratio"]), "Unit": "-"},
                {"Parameter": "Water content", "Value": str(mix["water_content_kg_m3"]), "Unit": "kg/m3"},
                {"Parameter": "Cement content", "Value": str(mix["cement_content_kg_m3"]), "Unit": "kg/m3"},
                {"Parameter": "Fine aggregate", "Value": str(mix["fine_agg_content_kg_m3"]), "Unit": "kg/m3"},
                {"Parameter": "Coarse aggregate", "Value": str(mix["coarse_agg_content_kg_m3"]), "Unit": "kg/m3"},
                {"Parameter": "Admixture dosage", "Value": str(mix["admixture_dosage_pct"]), "Unit": "%"},
                {"Parameter": "Water adjustment", "Value": str(mix["field_water_adjustment_kg"]), "Unit": "kg/m3"},
                {"Parameter": "Mix proportion", "Value": str(mix["mix_proportion_by_weight"]), "Unit": "by wt"},
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
            preview_key = f"recalc_preview_{slug}"
            if st.button("Preview Recalculated Mix", key=f"preview_btn_{slug}"):
                r = api_post(
                    f"/mixes/{slug}/recalculate/preview",
                    json={"parameter": parameter, "new_value": float(new_value), "save_revision": False},
                    timeout=20,
                )
                if r.status_code == 200:
                    st.session_state[preview_key] = {
                        "parameter": parameter,
                        "new_value": float(new_value),
                        "response": r.json(),
                        "source": "api",
                    }
                elif r.status_code == 404:
                    preview_mix, preview_warnings = local_recalc_preview(mix, parameter, float(new_value))
                    st.session_state[preview_key] = {
                        "parameter": parameter,
                        "new_value": float(new_value),
                        "response": {"updated_mix": preview_mix, "warnings": preview_warnings},
                        "source": "local_fallback",
                    }
                    st.info("Using local preview mode because backend preview endpoint is unavailable.")
                else:
                    st.error(r.text)

            preview_state = st.session_state.get(preview_key)
            if preview_state:
                preview_mix = preview_state["response"]["updated_mix"]
                st.markdown("#### Preview (Not Saved Yet)")
                preview_rows = [
                    {"Parameter": "Grade of concrete", "Value": str(preview_mix["concrete_grade"]), "Unit": "-"},
                    {"Parameter": "Target mean strength", "Value": str(preview_mix["target_mean_strength"]), "Unit": "MPa"},
                    {"Parameter": "Water-cement ratio", "Value": str(preview_mix["water_cement_ratio"]), "Unit": "-"},
                    {"Parameter": "Water content", "Value": str(preview_mix["water_content_kg_m3"]), "Unit": "kg/m3"},
                    {"Parameter": "Cement content", "Value": str(preview_mix["cement_content_kg_m3"]), "Unit": "kg/m3"},
                    {"Parameter": "Fine aggregate", "Value": str(preview_mix["fine_agg_content_kg_m3"]), "Unit": "kg/m3"},
                    {"Parameter": "Coarse aggregate", "Value": str(preview_mix["coarse_agg_content_kg_m3"]), "Unit": "kg/m3"},
                    {"Parameter": "Admixture dosage", "Value": str(preview_mix["admixture_dosage_pct"]), "Unit": "%"},
                    {"Parameter": "Water adjustment", "Value": str(preview_mix["field_water_adjustment_kg"]), "Unit": "kg/m3"},
                    {"Parameter": "Mix proportion", "Value": str(preview_mix["mix_proportion_by_weight"]), "Unit": "by wt"},
                ]
                st.table(preview_rows)

                preview_warnings = preview_state["response"].get("warnings", [])
                if preview_warnings:
                    for warning_msg in preview_warnings:
                        st.warning(warning_msg)

                save_option = st.radio(
                    "Save option",
                    ["Modify current mix", "Save as new mix design"],
                    key=f"save_option_{slug}",
                )

                if save_option == "Modify current mix":
                    if st.button("Save Changes to Current Mix", key=f"save_overwrite_{slug}"):
                        payload = {
                            "parameter": preview_state["parameter"],
                            "new_value": preview_state["new_value"],
                            "save_mode": "overwrite",
                            "save_revision": True,
                        }
                        res = api_post(f"/mixes/{slug}/recalculate/apply", json=payload, timeout=25)
                        if res.status_code == 200:
                            out = res.json()
                            st.success(f"Saved changes to mix {out['saved_mix']['mix_id']}.")
                            st.session_state.pop(preview_key, None)
                            st.query_params["slug"] = out["saved_mix"]["slug"]
                            st.rerun()
                        elif res.status_code == 404 and preview_state.get("source") == "local_fallback":
                            update_payload = {f: preview_mix[f] for f in UPDATE_FIELDS if f in preview_mix}
                            upd = api_put(f"/mixes/{slug}", json=update_payload, timeout=25)
                            if upd.status_code == 200:
                                saved = upd.json()
                                st.success(f"Saved changes to mix {saved['mix_id']}.")
                                st.session_state.pop(preview_key, None)
                                st.query_params["slug"] = saved["slug"]
                                st.rerun()
                            else:
                                st.error(upd.text)
                        else:
                            st.error(res.text)
                else:
                    default_new_mix_id = f"{mix['mix_id']}-R1"
                    default_new_slug = f"{mix['slug']}-r1"
                    default_new_name = f"{mix['mix_name']} (Recalculated)"
                    new_mix_id = st.text_input("New Mix ID", value=default_new_mix_id, key=f"new_mix_id_{slug}")
                    new_slug = st.text_input("New Slug", value=default_new_slug, key=f"new_slug_{slug}")
                    new_mix_name = st.text_input("New Mix Name", value=default_new_name, key=f"new_name_{slug}")

                    if st.button("Save as New Mix Design", key=f"save_new_mix_{slug}"):
                        payload = {
                            "parameter": preview_state["parameter"],
                            "new_value": preview_state["new_value"],
                            "save_mode": "new_mix",
                            "new_mix_id": new_mix_id.strip(),
                            "new_slug": new_slug.strip(),
                            "new_mix_name": new_mix_name.strip(),
                            "save_revision": True,
                        }
                        res = api_post(f"/mixes/{slug}/recalculate/apply", json=payload, timeout=25)
                        if res.status_code == 200:
                            out = res.json()
                            st.success(f"Saved as new mix {out['saved_mix']['mix_id']}.")
                            st.session_state.pop(preview_key, None)
                            st.query_params["slug"] = out["saved_mix"]["slug"]
                            st.rerun()
                        elif res.status_code == 404 and preview_state.get("source") == "local_fallback":
                            create_payload = {f: preview_mix[f] for f in CREATE_FIELDS if f in preview_mix}
                            create_payload["mix_id"] = new_mix_id.strip()
                            create_payload["slug"] = new_slug.strip()
                            create_payload["mix_name"] = new_mix_name.strip()
                            cre = api_post("/mixes", json=create_payload, timeout=25)
                            if cre.status_code == 200:
                                saved = cre.json()
                                st.success(f"Saved as new mix {saved['mix_id']}.")
                                st.session_state.pop(preview_key, None)
                                st.query_params["slug"] = saved["slug"]
                                st.rerun()
                            else:
                                st.error(cre.text)
                        else:
                            st.error(res.text)

        with c2:
            st.markdown("### QR")
            try:
                qr_params = {"base_url": QR_PUBLIC_BASE_URL} if QR_PUBLIC_BASE_URL else None
                qr_resp = api_get(f"/mixes/{slug}/qr/png", timeout=20, params=qr_params)
                if qr_resp.status_code == 200:
                    st.image(qr_resp.content, caption=f"QR for {slug}")
                else:
                    st.warning("QR could not be loaded.")
            except requests.RequestException:
                st.warning("QR could not be loaded.")

            st.markdown("### Downloads")
            render_download_button("Download CSV", f"/mixes/{slug}/export/csv", f"{slug}.csv", "text/csv")
            render_download_button(
                "Download Excel",
                f"/mixes/{slug}/export/xlsx",
                f"{slug}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            render_download_button("Download PDF", f"/mixes/{slug}/export/pdf", f"{slug}.pdf", "application/pdf")
            qr_params = {"base_url": QR_PUBLIC_BASE_URL} if QR_PUBLIC_BASE_URL else None
            render_download_button("Download QR PNG", f"/mixes/{slug}/qr/png", f"{slug}.png", "image/png", params=qr_params)
            render_download_button("Download QR SVG", f"/mixes/{slug}/qr/svg", f"{slug}.svg", "image/svg+xml", params=qr_params)
    else:
        st.error("Mix not found")

st.markdown("---")
st.markdown("### Bulk Import")
upload = st.file_uploader("Upload CSV or XLSX", type=["csv", "xlsx"])
if upload and st.button("Run Import"):
    files = {"file": (upload.name, upload.getvalue(), upload.type)}
    r = api_post("/mixes/import", files=files, timeout=60)
    if r.status_code == 200:
        out = r.json()
        st.success(f"Imported {out['imported']} of {out['total_rows']} rows")
    else:
        st.error(r.text)

st.markdown("### Database Exports")
render_download_button(
    "Download QR Sheet PDF",
    "/mixes/qr/sheet?limit=60",
    "qr-sheet.pdf",
    "application/pdf",
    timeout=60,
)
render_download_button(
    "Export Full Database JSON",
    "/mixes/database/export",
    "mix-database.json",
    "application/json",
    timeout=60,
)
