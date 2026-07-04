# tikpull

Download TikTok videos from the command line or as a Python library.

## Installation

```bash
uv pip install tikpull
```

## CLI usage

```bash
# Single video
tikpull https://www.tiktok.com/@user/video/123456

# Multiple videos
tikpull https://... https://...

# Batch from file (one URL per line)
tikpull -f urls.txt -o ./downloads
```

## Python API

```python
from tikpull import download_video, download_batch, DownloadRequest
from pathlib import Path

# Single download
result = download_video(DownloadRequest(
    url="https://www.tiktok.com/@user/video/123456",
    output_dir=Path("./downloads"),
))
print(result.output_path)

# Batch download
requests = [DownloadRequest(url=u) for u in ["https://...", "https://..."]]
results = download_batch(requests)
```

## Development

```bash
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pytest
```
