from pathlib import Path

import yt_dlp

from .models import DownloadRequest, DownloadResult


def _build_ydl_opts(request: DownloadRequest) -> dict:
    output_dir = request.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if request.filename:
        outtmpl = str(output_dir / request.filename)
    else:
        outtmpl = str(output_dir / "%(uploader)s_%(id)s.%(ext)s")

    return {
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        # Keep original quality; no re-encoding
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
    }


def download_video(request: DownloadRequest) -> DownloadResult:
    """Download a single TikTok video. Returns a DownloadResult."""
    opts = _build_ydl_opts(request)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            filename = ydl.prepare_filename(info)
            # yt-dlp may change the extension after merging
            output_path = Path(filename).with_suffix(".mp4")
            return DownloadResult(url=request.url, success=True, output_path=output_path)
    except yt_dlp.utils.DownloadError as exc:
        return DownloadResult(url=request.url, success=False, error=str(exc))


def download_batch(requests: list[DownloadRequest]) -> list[DownloadResult]:
    """Download multiple videos sequentially. Returns one result per request."""
    return [download_video(req) for req in requests]
