# tikpull

Download TikTok videos and photo carousels from the command line or as a Python library.

## Features

- Download TikTok videos (MP4, no watermark)
- Download TikTok photo/carousel posts (JPEG, no watermark)
- Batch download from a URL list file
- Automatically comments out successfully downloaded URLs in the list file (for easy resuming)
- Configurable output directory via config file or CLI flag

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

## Configuration

tikpull looks for a config file at `~/.config/tikpull/config.toml`:

```toml
output_dir = "~/Downloads/tiktok"
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

| URL type | Backend |
|---|---|
| `/video/` | yt-dlp (fallback: tikwm API) |
| `/photo/` | tikwm API (images downloaded as individual JPEGs) |

## Development

```bash
git clone https://github.com/RonanFromBrittany/tikpull.git
cd tikpull
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
```
