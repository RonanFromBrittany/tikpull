# tikpull

[![Security Scan](https://github.com/RonanFromBrittany/tikpull/actions/workflows/security.yml/badge.svg)](https://github.com/RonanFromBrittany/tikpull/actions/workflows/security.yml)

Download TikTok videos and photo carousels from the command line, as a Python library, or via a web interface.

## Features

- Download TikTok videos (MP4, no watermark)
- Download TikTok photo/carousel posts (JPEG, no watermark)
- Batch download from a URL list file
- Automatically comments out successfully downloaded URLs in the list file (for easy resuming)
- Configurable output directory and default URL file via config file or CLI flag
- Web interface with real-time progress, batch upload, and persistent download history
- Security scanning via CodeQL and pip-audit on every push

## Installation

```bash
uv pip install tikpull
```

## CLI usage

```bash
# Single video
tikpull "https://www.tiktok.com/@user/video/123456"

# Single photo/carousel post
tikpull "https://www.tiktok.com/@user/photo/123456"

# Custom output directory
tikpull -o ~/Downloads "https://www.tiktok.com/@user/video/123456"

# Batch download from a file (one URL per line)
tikpull -f urls.txt

# Combine: batch + custom output directory
tikpull -f urls.txt -o ~/Downloads/tiktok
```

### URL file format

```
https://www.tiktok.com/@user1/video/111
# https://www.tiktok.com/@user2/video/222   ← already downloaded, skipped
https://www.tiktok.com/@user3/photo/333
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

## Configuration

tikpull looks for a config file at `~/.config/tikpull/config.toml`:

```toml
output_dir = "~/Downloads/tiktok"
url_file   = "~/Documents/tiktok_urls.txt"
```

Priority order for the output directory:
1. `-o` / `--output` CLI flag
2. `output_dir` in `~/.config/tikpull/config.toml`
3. Current directory (fallback)

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

| URL type   | Backend                          |
|------------|----------------------------------|
| `/video/`  | yt-dlp (fallback: tikwm API)     |
| `/photo/`  | tikwm API (JPEG images)          |

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
