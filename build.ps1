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

Write-Host "=== portable readme ===" -ForegroundColor Cyan
$readme = @"
WEATHER APP PRO (portable)

Run WeatherAppPro.exe.

The first start asks for a free OpenWeatherMap API key
(create one at openweathermap.org/appid; new keys can take up to
two hours to activate). The key is stored in your user data folder
and never leaves your machine except in requests to OpenWeather.

Alternatively, put a .env file next to WeatherAppPro.exe containing
a line like:  OPENWEATHER_API_KEY=yourkey

Your data (key, settings, favorites, cache, logs) lives in
%LOCALAPPDATA%\WeatherAppPro. Delete that folder to reset.
"@
Set-Content -Path "dist\WeatherAppPro\README-portable.txt" -Value $readme

Write-Host "=== portable zip ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path release | Out-Null
$zip = "release\WeatherAppPro-portable.zip"
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path dist\WeatherAppPro -DestinationPath $zip

Write-Host "=== installer info page ===" -ForegroundColor Cyan
$privacy = Get-Content -Path "PRIVACY.md" -Raw
$info = @"
WEATHER APP PRO - PLEASE READ BEFORE INSTALLING

1) AN API KEY IS REQUIRED
   Weather App Pro needs your own FREE OpenWeatherMap API key.
   Create one at openweathermap.org/appid (new keys can take up to
   two hours to activate). The app asks for it on first start.

2) WEATHER DATA AND ATTRIBUTION
   Weather data is provided by OpenWeather (openweathermap.org).
   OpenWeatherMap's terms require visible attribution, which the app
   shows in its footer. Data accuracy is not warranted; do not rely
   on it for safety-critical decisions.

3) PRIVACY IN SHORT
   The app sends only your typed city queries and your own API key to
   OpenWeatherMap over HTTPS. Everything else (your key, settings,
   favorites, cache, logs) stays on your machine in
   %LOCALAPPDATA%\WeatherAppPro. The developer collects nothing.
   Full details below and in PRIVACY.md.

------------------------------------------------------------
PRIVACY DETAILS (PRIVACY.md)
------------------------------------------------------------

$privacy
"@
Set-Content -Path "installer\install-info.txt" -Value $info

Write-Host "=== installer (inno setup) ===" -ForegroundColor Cyan
$isccPaths = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$iscc = $isccPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw "Inno Setup 6 not found (install from jrsoftware.org)" }

$version = (Get-Content -Path "VERSION" -Raw).Trim()
& $iscc "/DAppVersion=$version" "installer\weatherapp.iss"
if ($LASTEXITCODE -ne 0) { throw "installer compile failed" }

Write-Host "done: $zip and release\WeatherAppPro-setup-$version.exe" -ForegroundColor Green
