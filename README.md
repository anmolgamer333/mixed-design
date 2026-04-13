# Concrete Mix Design Management Platform

Professional web application for concrete mix design database management with QR-based access, downloadable mix tables, revision tracking, and engineering-aware recalculation.

## Stack

- Frontend: React + TypeScript + Vite
- Backend: FastAPI + SQLAlchemy
- Database: PostgreSQL (configured), SQLite compatible for quick local tests
- QR: `qrcode` with PNG and SVG generation
- Exports: CSV, XLSX, PDF

## Key Features

- Ready-reference database with 60 preloaded mix designs
- Search, filter, sort, category and status views
- Unique permanent QR for every mix design
- QR scan opens exact detail page (`/mixes/{slug}`)
- Mix detail page with engineering table + units
- Exports: CSV, Excel, PDF + print + share link + QR downloads
- Admin actions: add, edit, delete, duplicate, regenerate QR, bulk import, full DB export
- Recalculation module with dependent update logic and warning panel
- Revision history saved after recalculation
- QR sheet generation for multi-QR printing
- Sample bulk import file and sample detail record included
- API tests for CRUD, QR, export, and recalculation revisions

## Project Structure

- `backend/` FastAPI app, database models, services, API routes, tests
- `frontend/` React TypeScript app with dashboard/list/detail/admin pages
- `docker-compose.yml` PostgreSQL service

## Database Tables

Implemented:

- `mix_designs`
- `mix_revisions`
- `materials`
- `admixtures`
- `qr_codes`
- `users`
- `export_logs`

## Run Instructions

### 1. Start PostgreSQL

```bash
docker compose up -d postgres
```

### 2. Backend setup

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Notes:

- On startup, schema is created and 60 sample mixes are seeded.
- QR files are generated under `backend/generated/qr`.

### 3. Frontend setup

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Frontend runs on `http://localhost:5173` and targets backend at `http://localhost:8000/api`.

### 4. Streamlit Deployment

This repository includes a Streamlit UI (`streamlit_app.py`) that connects to the FastAPI backend.

Local run:

```bash
pip install -r streamlit_requirements.txt
$env:API_BASE_URL="http://localhost:8000/api"   # PowerShell
streamlit run streamlit_app.py
```

For Streamlit Cloud:

1. Set app file to `streamlit_app.py`
2. Set Python dependencies file to `streamlit_requirements.txt`
3. Add environment variable `API_BASE_URL` pointing to your hosted FastAPI URL

## API Highlights

- `GET /api/mixes` list with search/filter/sort/pagination
- `GET /api/mixes/{slug}` detail by permanent slug
- `POST /api/mixes` create
- `PUT /api/mixes/{slug}` update
- `DELETE /api/mixes/{slug}` delete
- `POST /api/mixes/{slug}/duplicate`
- `POST /api/mixes/{slug}/recalculate`
- `GET /api/mixes/{slug}/revisions`
- `GET /api/mixes/{slug}/qr/png`
- `GET /api/mixes/{slug}/qr/svg`
- `POST /api/mixes/qr/regenerate-all`
- `GET /api/mixes/qr/sheet`
- `POST /api/mixes/import` CSV/XLSX bulk import
- `GET /api/mixes/{slug}/export/csv|xlsx|pdf`
- `GET /api/mixes/database/export`

## Preloaded and Sample Assets

- Seeded records: 60 mixes (`MX-0001` to `MX-0060`)
- Sample bulk import file: `backend/sample_data/mix_bulk_import_sample.csv`
- Sample detail reference: `backend/sample_data/sample_mix_detail_page.md`

## Test Cases

Run backend tests:

```bash
cd backend
pytest -q
```

Covers:

- CRUD/list behavior
- QR generation endpoint
- CSV/XLSX/PDF export endpoints
- Recalculation + revision creation

## Engineering Logic Notes

- Recalculation logic is isolated in `backend/app/services/calculation.py`.
- Export table logic is isolated in `backend/app/services/exporter.py`.
- QR logic is isolated in `backend/app/services/qr.py`.
- Constraint warnings are returned when recalculated values become impractical.

## Demo QR-linked Record Example

- Frontend detail URL: `http://localhost:5173/mixes/mix-0001`
- Direct QR image: `http://localhost:8000/api/mixes/mix-0001/qr/png`

## Screenshots

The seeded dataset and pages are demo-ready for screenshots immediately after running backend and frontend.
