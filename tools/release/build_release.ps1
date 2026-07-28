$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Python = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (!(Test-Path $Python)) {
    $Python = "python"
}
Push-Location $Root
try {
    & $Python tools\release\build_release.py
} finally {
    Pop-Location
}
