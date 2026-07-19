# tikpull

[![Security Scan](https://github.com/RonanFromBrittany/tikpull/actions/workflows/security.yml/badge.svg)](https://github.com/RonanFromBrittany/tikpull/actions/workflows/security.yml)

Download TikTok, YouTube, and Instagram videos (and TikTok photo carousels)
from the command line, as a Python library, or via a web/desktop interface.

## Features

- Download TikTok videos (MP4, no watermark) and photo/carousel posts (JPEG, no watermark)
- Download YouTube videos
- Download Instagram videos (reels, posts — public content)
- Batch download from a URL list file, mixing platforms freely
- Automatically comments out successfully downloaded URLs in the list file (for easy resuming)
- Configurable output directory and default URL file via config file or CLI flag
- Web interface with real-time progress, batch upload, and persistent download history
- Native desktop app (macOS / Windows installers) — no terminal required
- Security scanning via CodeQL and pip-audit on every push

> Downloading content is subject to each platform's Terms of Service and the
> rights of the content owner. This tool is intended for personal use with
> content you have the right to download (e.g. your own videos, or others
> shared with permission).

## Installation

```bash
uv pip install tikpull
```

### Desktop installers (macOS / Windows)

Prebuilt installers are published on the [Releases page](https://github.com/RonanFromBrittany/tikpull/releases):

- **macOS**: `tikpull.dmg` — open it, drag tikpull into Applications.
- **Windows**: `tikpull-setup.exe` — run it, follow the installer.

These give you a native tikpull window (see [Desktop app](#desktop-app)
below) with no Python install required.

## CLI usage

```bash
# TikTok video
tikpull "https://www.tiktok.com/@user/video/123456"

# TikTok photo/carousel post
tikpull "https://www.tiktok.com/@user/photo/123456"

# YouTube video
tikpull "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Instagram reel / post
tikpull "https://www.instagram.com/reel/Cabc123XYZ/"

# Custom output directory
tikpull -o ~/Downloads "https://www.tiktok.com/@user/video/123456"

# Batch download from a file (one URL per line, platforms can be mixed)
tikpull -f urls.txt

# Combine: batch + custom output directory
tikpull -f urls.txt -o ~/Downloads/tiktok
```

### URL file format

```
https://www.tiktok.com/@user1/video/111
# https://www.tiktok.com/@user2/video/222   ← already downloaded, skipped
https://www.tiktok.com/@user3/photo/333
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://www.instagram.com/reel/Cabc123XYZ/
```

Lines starting with `#` are ignored. After each successful download, the
corresponding line is automatically commented out so you can safely resume
an interrupted batch.

## Web interface

```bash
tikpull-web
```

Opens a local web server at `http://127.0.0.1:8080` with:

- Single URL download with real-time progress
- Batch download via drag-and-drop URL file upload
- Persistent download history (SQLite, survives restarts)
- Settings page to configure output directory and default URL file
- A button to open the downloads folder directly from the interface

## Desktop app

tikpull can also run in a native window instead of a browser tab, using
[pywebview](https://pywebview.flowrl.com/).

```bash
pip install "tikpull[desktop]"
tikpull-desktop
```

### Building the installers yourself

You don't need to do this to just use tikpull — see
[Desktop installers](#desktop-installers-macos--windows) above for prebuilt
downloads. These steps are only for building them yourself.

#### macOS

Run this on a Mac:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[desktop]" pyinstaller
bash packaging/macos/build.sh
```

Produces `dist/tikpull.app` and `dist/tikpull.dmg`. Since the app isn't
code-signed, the first launch will be blocked by Gatekeeper — right-click
the app and choose **Open** (or allow it via System Settings -> Privacy &
Security) the first time only.

#### Windows

Run this on Windows, with [Inno Setup](https://jrsoftware.org/isinfo.php)
installed:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[desktop]" pyinstaller
powershell -ExecutionPolicy Bypass -File packaging\windows\build.ps1
iscc packaging\windows\installer.iss
```

Produces `dist_installer\tikpull-setup.exe`.

#### Automated builds (GitHub Actions)

Pushing a version tag builds both installers and publishes them as a
GitHub Release automatically:

```bash
git tag v0.2.0
git push --tags
```

You can also trigger a build without publishing a release from the
**Actions** tab -> **Release** -> **Run workflow** (the installers are then
attached to that workflow run instead).

## Configuration

tikpull looks for a config file at `~/.config/tikpull/config.toml`:

```toml
output_dir = "~/Downloads/tiktok"
url_file   = "~/Documents/tiktok_urls.txt"
```

Priority order for the output directory:
1. `-o` / `--output` CLI flag
2. `output_dir` in `~/.config/tikpull/config.toml`
3. `~/Downloads/tikpull` (fallback)

## Python API

```python
from tikpull import download_video, download_batch, DownloadRequest
from pathlib import Path

# Single video
result = download_video(DownloadRequest(
    url="https://www.tiktok.com/@user/video/123456",
    output_dir=Path("./downloads"),
))
print(result.success, result.output_path)

# Batch download
requests = [
    DownloadRequest(url="https://www.tiktok.com/@user/video/111"),
    DownloadRequest(url="https://www.tiktok.com/@user/photo/222"),
]
results = download_batch(requests)
```

## How it works

| Platform                | Backend                      |
|--------------------------|------------------------------|
| TikTok video (`/video/`) | yt-dlp (fallback: tikwm API) |
| TikTok photo (`/photo/`) | tikwm API (JPEG images)      |
| YouTube                  | yt-dlp                       |
| Instagram                | yt-dlp                       |

Anything else yt-dlp supports may also work, but only TikTok, YouTube, and
Instagram are actively tested. Instagram content behind a private account,
or some post types, may require you to be logged in — not currently
supported.

## Development

```bash
git clone https://github.com/RonanFromBrittany/tikpull.git
cd tikpull
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
```

## Security

This project runs automated security scans on every push:

- **CodeQL** — static analysis of Python source code
- **pip-audit** — vulnerability scan of all third-party dependencies
- **Dependabot** — automatic alerts for newly published CVEs

Results are visible in the [Security tab](https://github.com/RonanFromBrittany/tikpull/security).
