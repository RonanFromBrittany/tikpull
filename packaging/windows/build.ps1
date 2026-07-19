# Build tikpull.exe for Windows with PyInstaller.
#
# Run this on Windows, from the project root, inside a venv with the
# desktop extras installed:
#
#   python -m venv .venv
#   .venv\Scripts\activate
#   pip install -e ".[desktop]" pyinstaller
#   powershell -ExecutionPolicy Bypass -File packaging\windows\build.ps1
#
# Produces dist\tikpull\tikpull.exe. packaging\windows\installer.iss then
# wraps that folder into a proper Setup.exe installer (see the main
# README's "Windows installer" section, or run it directly with Inno
# Setup's ISCC.exe).

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..\..")

Remove-Item -Recurse -Force build, dist, tikpull.spec -ErrorAction SilentlyContinue

pyinstaller `
  --name tikpull `
  --windowed `
  --icon packaging\windows\icon.ico `
  --paths src `
  --add-data "src/tikpull/web/static;tikpull/web/static" `
  --collect-all uvicorn `
  --collect-all fastapi `
  --collect-all imageio_ffmpeg `
  --noconfirm `
  src\tikpull\desktop.py

Write-Host ""
Write-Host "Done. dist\tikpull\tikpull.exe is ready."
Write-Host "Next: compile packaging\windows\installer.iss with Inno Setup to build the installer."
