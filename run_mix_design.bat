@echo off
cd /d %~dp0

echo Starting Mix Design backend on http://127.0.0.1:8001 ...
start "mix-backend" cmd /c "cd /d backend && set DATABASE_URL=sqlite:///./mix_designs.db && set BASE_PUBLIC_URL=http://127.0.0.1:8501 && python -m uvicorn app.main:app --host 127.0.0.1 --port 8001"

timeout /t 4 >nul

echo Starting Mix Design Streamlit on http://127.0.0.1:8501 ...
set API_BASE_URL=http://127.0.0.1:8001/api
set AUTO_START_BACKEND=0
python -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8501
