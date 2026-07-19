#!/usr/bin/env bash
# Build tikpull.app + tikpull.dmg for macOS with PyInstaller.
#
# Run this ON A MAC, from the project root, inside a venv that has the
# desktop extras installed:
#
#   python3 -m venv .venv
#   source .venv/bin/activate
#   pip install -e ".[desktop]" pyinstaller
#   bash packaging/macos/build.sh
#
# Produces dist/tikpull.app and dist/tikpull.dmg. Double-click the .dmg,
# drag tikpull into Applications.
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
  --collect-all imageio_ffmpeg \
  --noconfirm \
  src/tikpull/desktop.py

echo
echo "App built. Packaging into a .dmg..."

DMG_STAGING=$(mktemp -d)
trap 'rm -rf "$DMG_STAGING"' EXIT

cp -R dist/tikpull.app "$DMG_STAGING/"
ln -s /Applications "$DMG_STAGING/Applications"

rm -f dist/tikpull.dmg
hdiutil create \
  -volname "tikpull" \
  -srcfolder "$DMG_STAGING" \
  -ov -format UDZO \
  dist/tikpull.dmg

echo
echo "Done:"
echo "  - dist/tikpull.app  (drag to /Applications yourself)"
echo "  - dist/tikpull.dmg  (double-click, then drag tikpull into Applications)"
