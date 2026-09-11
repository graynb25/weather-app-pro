# One-command release build (release-plan item 1.4).
#
# Runs: tests, release assets (icon + version resource), the PyInstaller
# build, the secret scan, and zips the portable artifact.
#
# Run from the project root or anywhere:  powershell -File build.ps1

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "=== tests ===" -ForegroundColor Cyan
$env:QT_QPA_PLATFORM = "offscreen"
& .venv\Scripts\python.exe -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "tests failed" }

Write-Host "=== release assets (icon, version resource) ===" -ForegroundColor Cyan
$env:QT_QPA_PLATFORM = ""
& .venv\Scripts\python.exe tools\make_release_assets.py
if ($LASTEXITCODE -ne 0) { throw "asset generation failed" }

Write-Host "=== pyinstaller ===" -ForegroundColor Cyan
& .venv\Scripts\pyinstaller.exe app.spec --noconfirm --distpath dist --workpath build
if ($LASTEXITCODE -ne 0) { throw "pyinstaller failed" }

Write-Host "=== secret scan ===" -ForegroundColor Cyan
& .venv\Scripts\python.exe tools\secret_scan.py dist\WeatherAppPro
if ($LASTEXITCODE -ne 0) { throw "secret scan found key material" }

Write-Host "=== portable zip ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path release | Out-Null
$zip = "release\WeatherAppPro-portable.zip"
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path dist\WeatherAppPro -DestinationPath $zip

Write-Host "done: $zip" -ForegroundColor Green
