from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tikpull import DownloadRequest, DownloadResult, download_video


def test_download_success(tmp_path):
    fake_info = {"uploader": "user", "id": "abc123", "ext": "mp4"}
    fake_filename = str(tmp_path / "user_abc123.mp4")

    with patch("tikpull.downloader.yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = fake_info
        mock_ydl.prepare_filename.return_value = fake_filename

        request = DownloadRequest(url="https://tiktok.com/@user/video/123", output_dir=tmp_path)
        result = download_video(request)

    assert result.success is True
    assert result.output_path == Path(fake_filename).with_suffix(".mp4")
    assert result.error is None


def test_download_failure(tmp_path):
    import yt_dlp

    with patch("tikpull.downloader.yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.side_effect = yt_dlp.utils.DownloadError("404 not found")

        request = DownloadRequest(url="https://tiktok.com/@user/video/bad", output_dir=tmp_path)
        result = download_video(request)

    assert result.success is False
    assert result.error is not None
    assert result.output_path is None
