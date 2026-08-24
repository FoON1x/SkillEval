<#
.SYNOPSIS
  One-click start both SkillEval services (FastAPI backend + Vite frontend) in the background.
.DESCRIPTION
  Launches the backend (uvicorn) and frontend (vite) as background processes, saves their
  PIDs to .run/pids.json for stop-all.ps1, then waits for both to become healthy.
  Prerequisites: apps/api/.venv (run `uv sync` in apps/api) and apps/web/node_modules (run `npm install` in apps/web).
  By default uvicorn runs WITHOUT --reload for clean PID tracking; pass -Reload to enable it.
.PARAMETER BackendPort
  Port for the FastAPI backend (default 8000).
.PARAMETER FrontendPort
  Port for the Vite dev server (default 5173).
.PARAMETER Reload
  Enable uvicorn --reload (spawns a reloader child; stop-all.ps1 will kill the process tree).
.EXAMPLE
  .\scripts\start-all.ps1
  .\scripts\start-all.ps1 -Reload
#>
[CmdletBinding()]
param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [switch]$Reload
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$apiDir = Join-Path $repoRoot 'apps\api'
$webDir = Join-Path $repoRoot 'apps\web'
$runDir = Join-Path $repoRoot '.run'
$pidFile = Join-Path $runDir 'pids.json'

function Test-PortInUse([int]$port) {
    try { Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop | Out-Null; return $true }
    catch { return $false }
}

if (-not (Test-Path -LiteralPath $runDir)) {
    New-Item -ItemType Directory -Path $runDir -Force | Out-Null
}

$py = Join-Path $apiDir '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $py)) {
    Write-Error "Backend venv not found at $py. Run 'uv sync' in apps/api first."
    exit 1
}
if (-not (Test-Path -LiteralPath (Join-Path $webDir 'node_modules'))) {
    Write-Error "Frontend node_modules not found. Run 'npm install' in apps/web first."
    exit 1
}

if (Test-PortInUse $BackendPort) { Write-Error "Port $BackendPort already in use."; exit 1 }
if (Test-PortInUse $FrontendPort) { Write-Error "Port $FrontendPort already in use."; exit 1 }

# --- Start backend ---
# Use cmd /c so the .cmd shim runs correctly and the python process is a direct child of cmd.
$backendCmd = "`"$py`" -m uvicorn skill_eval.main:app --port $BackendPort"
if ($Reload) { $backendCmd += ' --reload' }
$backend = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c', $backendCmd) -WorkingDirectory $apiDir -PassThru -WindowStyle Hidden
Write-Host "Backend started (PID $($backend.Id)) on port $BackendPort$(if ($Reload) { ' [reload]' })"

# --- Start frontend ---
# npm resolves to npm.ps1 on this machine; npm.cmd is the reliable launcher for Start-Process.
$npmDir = Split-Path (Get-Command npm -ErrorAction Stop).Source
$npmCmd = Join-Path $npmDir 'npm.cmd'
if (-not (Test-Path -LiteralPath $npmCmd)) {
    Write-Error "npm.cmd not found next to npm ($npmDir)."
    exit 1
}
$frontend = Start-Process -FilePath 'cmd.exe' -ArgumentList @('/c', "`"$npmCmd`" run dev") -WorkingDirectory $webDir -PassThru -WindowStyle Hidden
Write-Host "Frontend started (PID $($frontend.Id)) on port $FrontendPort"

@{
    backend      = $backend.Id
    frontend     = $frontend.Id
    backendPort  = $BackendPort
    frontendPort = $FrontendPort
} | ConvertTo-Json | Set-Content -LiteralPath $pidFile -Encoding UTF8

# --- Health check ---
function Wait-Healthy([string]$url, [string]$name, [int]$timeout = 40) {
    $deadline = (Get-Date).AddSeconds($timeout)
    while ((Get-Date) -lt $deadline) {
        try { Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2 | Out-Null; Write-Host "$name ready."; return $true }
        catch { Start-Sleep -Milliseconds 500 }
    }
    Write-Warning "$name did not become healthy within ${timeout}s."
    return $false
}

Wait-Healthy "http://127.0.0.1:$BackendPort/health" 'Backend'
# Vite serves on the port; a HEAD request to root returns 200 (or 404) once it's up.
Wait-Healthy "http://localhost:$FrontendPort/" 'Frontend' 30

Write-Host "`nServices running. Open http://localhost:$FrontendPort`nRun scripts/stop-all.ps1 to stop."
