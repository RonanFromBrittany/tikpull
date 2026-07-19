#!/usr/bin/env bash
# Build tikpull.app for macOS with PyInstaller.
#
# Run this ON A MAC, from the project root, inside a venv that has the
# desktop extras installed:
#
#   python3 -m venv .venv
#   source .venv/bin/activate
#   pip install -e ".[desktop]" pyinstaller
#   bash packaging/macos/build.sh
#
# The finished app will be at dist/tikpull.app.
# Drag it into /Applications, then double-click to launch.
#
# Note: since the app isn't code-signed/notarized, the first launch will be
# blocked by Gatekeeper ("cannot be opened because the developer cannot be
# verified"). Right-click the app -> Open (or System Settings -> Privacy &
# Security -> "Open Anyway") the first time only.

set -euo pipefail
cd "$(dirname "$0")/../.."

rm -rf build dist tikpull.spec

pyinstaller \
  --name tikpull \
  --windowed \
  --icon packaging/macos/icon.icns \
  --osx-bundle-identifier com.ronanfrombrittany.tikpull \
  --paths src \
  --add-data "src/tikpull/web/static:tikpull/web/static" \
  --collect-all uvicorn \
  --collect-all fastapi \
  --noconfirm \
  src/tikpull/desktop.py

echo
echo "Done. Drag dist/tikpull.app to /Applications, then double-click to launch."
