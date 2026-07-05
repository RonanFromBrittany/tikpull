from pathlib import Path

import httpx
import yt_dlp

from .models import DownloadRequest, DownloadResult

TIKWM_API = "https://www.tikwm.com/api/"


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
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
    }


def _is_photo_url(url: str) -> bool:
    """Return True if the URL points to a TikTok photo/carousel post."""
    return "/photo/" in url


def _post_id(url: str) -> str:
    """Extract the post ID from a TikTok URL."""
    return url.rstrip("/").split("/")[-1].split("?")[0]


def _download_with_ytdlp(request: DownloadRequest) -> DownloadResult:
    """Attempt download using yt-dlp."""
    opts = _build_ydl_opts(request)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            filename = ydl.prepare_filename(info)
            output_path = Path(filename).with_suffix(".mp4")
            return DownloadResult(url=request.url, success=True, output_path=output_path)
    except yt_dlp.utils.DownloadError as exc:
        return DownloadResult(url=request.url, success=False, error=str(exc))


def _download_with_tikwm(request: DownloadRequest) -> DownloadResult:
    """Download a photo/carousel post via the tikwm API.

    - If the post contains images, downloads each one as a JPEG.
    - Falls back to the MP4 play URL if no images are found.
    """
    output_dir = request.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    post_id = _post_id(request.url)

    try:
        resp = httpx.post(TIKWM_API, data={"url": request.url, "hd": 1}, timeout=15)
        resp.raise_for_status()
        data = resp.json().get("data", {})

        images = data.get("images", [])

        if images:
            # Download each image as an individual JPEG file
            output_paths = []
            for idx, img_url in enumerate(images, start=1):
                filename = request.filename or f"photo_{post_id}_{idx:02d}.jpg"
                output_path = output_dir / filename
                content = httpx.get(img_url, follow_redirects=True, timeout=30).content
                output_path.write_bytes(content)
                output_paths.append(output_path)
            # Return the first image path as the primary output
            return DownloadResult(url=request.url, success=True, output_path=output_paths[0])

        # Fallback: download as MP4 if tikwm provides a play URL
        play_url = data.get("hdplay") or data.get("play")
        if play_url:
            filename = request.filename or f"photo_{post_id}.mp4"
            output_path = output_dir / filename
            content = httpx.get(play_url, follow_redirects=True, timeout=60).content
            output_path.write_bytes(content)
            return DownloadResult(url=request.url, success=True, output_path=output_path)

        return DownloadResult(
            url=request.url,
            success=False,
            error="tikwm: no images or play URL found in API response",
        )

    except Exception as exc:
        return DownloadResult(url=request.url, success=False, error=f"tikwm: {exc}")


def download_video(request: DownloadRequest) -> DownloadResult:
    """Download a single TikTok video or photo post.

    Strategy:
    - Photo/carousel URLs (/photo/) → tikwm API directly
    - Video URLs → yt-dlp first, tikwm as fallback on failure
    """
    if _is_photo_url(request.url):
        return _download_with_tikwm(request)

    result = _download_with_ytdlp(request)
    if not result.success:
        result = _download_with_tikwm(request)
    return result


def download_batch(requests: list[DownloadRequest]) -> list[DownloadResult]:
    """Download multiple videos sequentially. Returns one result per request."""
    return [download_video(req) for req in requests]
