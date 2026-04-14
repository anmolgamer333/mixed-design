@echo off
cd /d %~dp0

echo Clearing old ports (8001 backend / 8501 streamlit)...
for /f "tokens=5" %%p in ('netstat -aon ^| findstr :8001') do taskkill /PID %%p /F >nul 2>nul
for /f "tokens=5" %%p in ('netstat -aon ^| findstr :8501') do taskkill /PID %%p /F >nul 2>nul

echo Starting Mix Design backend on http://127.0.0.1:8001 ...
start "mix-backend" /min cmd /k "cd /d backend && set DATABASE_URL=sqlite:///./mix_designs.db && set BASE_PUBLIC_URL=http://127.0.0.1:8501 && python -m uvicorn app.main:app --host 127.0.0.1 --port 8001"

timeout /t 5 >nul

echo Starting Mix Design Streamlit on http://127.0.0.1:8501 ...
set API_BASE_URL=http://127.0.0.1:8001/api
set AUTO_START_BACKEND=0
python -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8501
