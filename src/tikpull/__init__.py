"""tikpull — download TikTok videos via CLI or Python API."""

from .downloader import download_batch, download_video
from .models import DownloadRequest, DownloadResult

__all__ = ["download_video", "download_batch", "DownloadRequest", "DownloadResult"]
__version__ = "0.1.0"
