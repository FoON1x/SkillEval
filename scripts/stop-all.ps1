<#
.SYNOPSIS
  One-click stop both SkillEval services started by start-all.ps1.
.DESCRIPTION
  Reads PIDs from .run/pids.json and stops the tracked backend/frontend processes AND their
  child trees (covers uvicorn --reload reloader children and cmd /c wrappers). Falls back to
  killing any process listening on the configured ports. Removes .run/pids.json when done.
.PARAMETER BackendPort
  Port to clear as a fallback (default 8000).
.PARAMETER FrontendPort
  Port to clear as a fallback (default 5173).
.EXAMPLE
  .\scripts\stop-all.ps1
#>
[CmdletBinding()]
param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$pidFile = Join-Path $repoRoot '.run\pids.json'

function Get-ChildPids([int]$rootPid, [int]$depth = 0) {
    # Recursively collect descendant PIDs via WMI parent links.
    if ($depth -gt 6) { return @() }
    $children = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.ParentProcessId -eq $rootPid } |
        ForEach-Object { $_.ProcessId })
    $result = @($children)
    foreach ($c in $children) { $result += Get-ChildPids $c ($depth + 1) }
    return $result
}

function Stop-Tree([int]$rootPid) {
    $pidsToKill = @($rootPid) + (Get-ChildPids $rootPid)
    foreach ($id in ($pidsToKill | Sort-Object -Descending -Unique)) {
        if (Get-Process -Id $id -ErrorAction SilentlyContinue) {
            try { Stop-Process -Id $id -Force -ErrorAction Stop } catch { }
        }
    }
}

function Stop-ByPort([int]$port) {
    try {
        $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop
        foreach ($c in $conns) {
            $owner = $c.OwningProcess
            if ($owner -and (Get-Process -Id $owner -ErrorAction SilentlyContinue)) {
                try { Stop-Tree $owner; Write-Host "Killed process tree on port $port (root PID $owner)." }
                catch { Write-Warning "Could not kill PID $owner on port ${port}: ${_}" }
            }
        }
    } catch { Write-Host "No process listening on port $port." }
}

$stopped = 0
if (Test-Path -LiteralPath $pidFile) {
    $pids = Get-Content -LiteralPath $pidFile -Raw | ConvertFrom-Json
    foreach ($key in 'backend', 'frontend') {
        $id = $pids.$key
        if ($id -and (Get-Process -Id $id -ErrorAction SilentlyContinue)) {
            try {
                Stop-Tree $id
                Write-Host "Stopped $key (PID $id) and its children."
                $stopped++
            } catch { Write-Warning "Could not stop $key (PID $id): ${_}" }
        }
    }
    Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
} else {
    Write-Host 'No PID file found (.run\pids.json); using port-based fallback.'
}

# Port fallback: covers orphaned children and runs started outside start-all.ps1.
Stop-ByPort $BackendPort
Stop-ByPort $FrontendPort

if ($stopped -eq 0 -and -not (Test-Path -LiteralPath $pidFile)) {
    Write-Host 'No tracked processes were running.'
}
Write-Host 'Done.'
