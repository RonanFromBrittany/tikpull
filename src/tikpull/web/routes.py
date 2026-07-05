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

router = APIRouter()

# Active URL file path for the current session (from config or upload)
_active_url_file: Path | None = None


class SingleURLRequest(BaseModel):
    url: str


def _result_to_dict(result: DownloadResult, already_downloaded: bool = False) -> dict:
    return {
        "url": result.url,
        "success": result.success,
        "output_path": str(result.output_path) if result.output_path else None,
        "error": result.error,
        "already_downloaded": already_downloaded,
    }


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
    """Comment out the line matching url in the file."""
    lines = path.read_text().splitlines()
    new_lines = [f"# {line}" if line.strip() == url else line for line in lines]
    path.write_text("\n".join(new_lines) + "\n")


async def _stream_downloads(
    urls: list[str],
    already_downloaded: list[str],
    url_file: Path | None,
) -> AsyncGenerator:
    """Yield SSE events for each download, prepending already-downloaded entries."""
    config = load_config()
    output_dir = get_output_dir(config)

    # Emit already-downloaded entries immediately
    for url in already_downloaded:
        entry = {
            "url": url,
            "success": True,
            "output_path": None,
            "error": None,
            "already_downloaded": True,
        }
        yield f"data: {json.dumps({'type': 'already_downloaded', 'url': url})}\n\n"

    yield f"data: {json.dumps({'type': 'start', 'total': len(urls)})}\n\n"

    for idx, url in enumerate(urls, start=1):
        yield f"data: {json.dumps({'type': 'progress', 'idx': idx, 'url': url})}\n\n"

        request = DownloadRequest(url=url, output_dir=output_dir)
        result = await asyncio.get_event_loop().run_in_executor(None, download_video, request)

        # Comment out the URL in the file immediately after a successful download
        if result.success and url_file is not None:
            _comment_url_in_file(url_file, url)

        entry = _result_to_dict(result)
        yield f"data: {json.dumps({'type': 'result', 'idx': idx, **entry})}\n\n"

    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@router.get("/history")
async def get_history():
    """Return already-downloaded URLs from the active URL file."""
    global _active_url_file

    # Refresh from config each time in case the file changed
    config = load_config()
    url_file = _active_url_file or get_url_file(config)

    if url_file is None or not url_file.is_file():
        return {"history": [], "url_file": None}

    _, commented_urls = _parse_url_file(url_file)
    history = [
        {"url": url, "success": True, "output_path": None, "error": None, "already_downloaded": True}
        for url in commented_urls
    ]
    return {"history": history, "url_file": str(url_file)}


@router.delete("/history")
async def clear_history():
    """Clear session state (does not modify the URL file)."""
    global _active_url_file
    _active_url_file = None
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

    Saves the uploaded file to a temp location so it can be updated in place
    as downloads complete (commented-out lines track progress).
    """
    global _active_url_file

    content = await file.read()

    # Save the uploaded file alongside the config-defined URL file, or use a temp path
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
