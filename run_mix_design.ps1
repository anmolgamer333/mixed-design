$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Stop-PortProcesses([int]$Port) {
  $lines = netstat -ano | Select-String (":" + $Port)
  $ids = @()
  foreach ($line in $lines) {
    $parts = (($line -replace "\s+", " ").Trim()).Split(" ")
    if ($parts.Length -ge 5) {
      $pidValue = $parts[-1]
      if ($pidValue -match '^[0-9]+$') {
        $ids += [int]$pidValue
      }
    }
  }
  $ids = $ids | Sort-Object -Unique
  foreach ($id in $ids) {
    try { Stop-Process -Id $id -Force -ErrorAction Stop } catch {}
  }
}

function Wait-Http200([string]$Url, [int]$Retries = 40, [int]$SleepMs = 750) {
  for ($i = 0; $i -lt $Retries; $i++) {
    try {
      $res = Invoke-WebRequest -UseBasicParsing $Url -TimeoutSec 2
      if ($res.StatusCode -eq 200) { return $true }
    } catch {}
    Start-Sleep -Milliseconds $SleepMs
  }
  return $false
}

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
  Write-Host "Python was not found in PATH for this shell." -ForegroundColor Red
  Write-Host "Install Python and ensure 'python' runs in this terminal." -ForegroundColor Yellow
  exit 1
}
$pythonExe = $pythonCmd.Source

Write-Host "Clearing old ports (8001 backend / 8501 streamlit)..." -ForegroundColor Cyan
Stop-PortProcesses -Port 8001
Stop-PortProcesses -Port 8501

$backendDir = Join-Path $root "backend"
Write-Host "Starting Mix Design backend on http://127.0.0.1:8001 ..." -ForegroundColor Green
$backendCmd = "cd /d `"$backendDir`" && set DATABASE_URL=sqlite:///./mix_designs.db && set BASE_PUBLIC_URL=http://127.0.0.1:8501 && `"$pythonExe`" -m uvicorn app.main:app --host 127.0.0.1 --port 8001"
Start-Process cmd.exe -ArgumentList "/k", $backendCmd -WindowStyle Minimized | Out-Null

Write-Host "Waiting for backend readiness..." -ForegroundColor Cyan
$ok = Wait-Http200 -Url "http://127.0.0.1:8001/api/mixes?page_size=1"
if (-not $ok) {
  Write-Host "Backend did not become ready in time." -ForegroundColor Red
  Write-Host "Please open the minimized 'mix-backend' PowerShell window and check errors." -ForegroundColor Yellow
  exit 1
}

$env:API_BASE_URL = "http://127.0.0.1:8001/api"
$env:AUTO_START_BACKEND = "0"

Write-Host "Starting Mix Design Streamlit on http://127.0.0.1:8501 ..." -ForegroundColor Green
& $pythonExe -m streamlit run (Join-Path $root "streamlit_app.py") --server.address 127.0.0.1 --server.port 8501
