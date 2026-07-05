"""API routes for tikpull web interface."""

import asyncio
import json
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from tikpull.config import load_config, get_output_dir, get_url_file
from tikpull.downloader import download_video
from tikpull.models import DownloadRequest, DownloadResult
from .database import record_download, get_history, clear_history

router = APIRouter()

# Active URL file path for the current session (from config or upload)
_active_url_file: Path | None = None


class SingleURLRequest(BaseModel):
    url: str


def _parse_url_file(path: Path) -> tuple[list[str], list[str]]:
    """Parse a URL file and return (active_urls, commented_urls).

    Active URLs are lines that are not commented out.
    Commented URLs are lines starting with '#' that contain a URL.
    """
    active_urls = []
    commented_urls = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            url = stripped.lstrip("#").strip()
            if url.startswith("http"):
                commented_urls.append(url)
        else:
            active_urls.append(stripped)
    return active_urls, commented_urls


def _comment_url_in_file(path: Path, url: str) -> None:
    """Comment out the first line whose stripped content matches url."""
    lines = path.read_text().splitlines()
    new_lines = []
    commented = False
    for line in lines:
        # Match on the base URL, ignoring query parameters for robustness
        base = line.strip().split("?")[0]
        url_base = url.split("?")[0]
        if not commented and base == url_base:
            new_lines.append(f"# {line.strip()}")
            commented = True
        else:
            new_lines.append(line)
    path.write_text("\n".join(new_lines) + "\n")


async def _stream_downloads(
    urls: list[str],
    already_downloaded: list[str],
    url_file: Path | None,
) -> AsyncGenerator:
    """Yield SSE events for each download, prepending already-downloaded entries."""
    config = load_config()
    output_dir = get_output_dir(config)

    # Emit already-downloaded entries from the URL file (commented lines)
    for url in already_downloaded:
        await record_download(url, status="already_downloaded")
        yield f"data: {json.dumps({'type': 'already_downloaded', 'url': url})}\n\n"

    yield f"data: {json.dumps({'type': 'start', 'total': len(urls)})}\n\n"

    for idx, url in enumerate(urls, start=1):
        yield f"data: {json.dumps({'type': 'progress', 'idx': idx, 'url': url})}\n\n"

        request = DownloadRequest(url=url, output_dir=output_dir)
        result = await asyncio.get_event_loop().run_in_executor(None, download_video, request)

        if result.success:
            # Comment out the URL in the file and record success in DB
            if url_file is not None:
                _comment_url_in_file(url_file, url)
            await record_download(
                url,
                status="success",
                output_path=str(result.output_path) if result.output_path else None,
            )
        else:
            await record_download(url, status="error", error=result.error)

        entry = {
            "url": result.url,
            "success": result.success,
            "output_path": str(result.output_path) if result.output_path else None,
            "error": result.error,
            "already_downloaded": False,
        }
        yield f"data: {json.dumps({'type': 'result', 'idx': idx, **entry})}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.get("/history")
async def get_history_route():
    """Return download history from the SQLite database."""
    history = await get_history()
    return {"history": history}


@router.delete("/history")
async def clear_history_route():
    """Clear the full download history from the database."""
    await clear_history()
    return {"status": "cleared"}


@router.post("/download/stream")
async def download_stream(body: SingleURLRequest):
    """Download a single URL with SSE progress stream."""
    config = load_config()
    url_file = _active_url_file or get_url_file(config)
    return StreamingResponse(
        _stream_downloads([body.url], [], url_file),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/download/batch")
async def download_batch_file(file: UploadFile = File(...)):
    """Upload a URL file and download all active entries via SSE stream.

    Saves the uploaded file to the path defined in config (url_file), or
    to ~/.config/tikpull/urls.txt as a fallback.
    """
    global _active_url_file

    content = await file.read()

    config = load_config()
    config_url_file = get_url_file(config)
    if config_url_file is not None:
        save_path = config_url_file
    else:
        save_path = Path.home() / ".config" / "tikpull" / "urls.txt"
        save_path.parent.mkdir(parents=True, exist_ok=True)

    save_path.write_bytes(content)
    _active_url_file = save_path

    active_urls, commented_urls = _parse_url_file(save_path)

    if not active_urls and not commented_urls:
        raise HTTPException(status_code=400, detail="No valid URLs found in file")

    return StreamingResponse(
        _stream_downloads(active_urls, commented_urls, save_path),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
