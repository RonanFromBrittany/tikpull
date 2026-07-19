"""Tests for TikTok/YouTube/Instagram URL routing in download_video()."""

from unittest.mock import MagicMock, patch

import yt_dlp

from tikpull import DownloadRequest, download_video
from tikpull.downloader import _is_photo_url, _is_tiktok_url


def test_is_tiktok_url_matches_tiktok_hosts():
    assert _is_tiktok_url("https://www.tiktok.com/@user/video/123") is True
    assert _is_tiktok_url("https://tiktok.com/@user/video/123") is True
    assert _is_tiktok_url("https://vm.tiktok.com/abc123/") is True


def test_is_tiktok_url_rejects_other_hosts():
    assert _is_tiktok_url("https://www.youtube.com/watch?v=abc") is False
    assert _is_tiktok_url("https://www.instagram.com/reel/abc/") is False
    assert _is_tiktok_url("https://nottiktok.com/photo/123") is False


def test_is_photo_url_only_true_for_tiktok():
    assert _is_photo_url("https://www.tiktok.com/@user/photo/123") is True
    # An unrelated site with "/photo/" in the path must not be treated as
    # a TikTok photo post (would otherwise be routed to the tikwm API).
    assert _is_photo_url("https://example.com/photo/123") is False


def test_youtube_download_uses_ytdlp_and_succeeds(tmp_path):
    fake_info = {"uploader": "channel", "id": "vid123", "ext": "mp4"}
    fake_filename = str(tmp_path / "channel_vid123.mp4")

    with patch("tikpull.downloader.yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = fake_info
        mock_ydl.prepare_filename.return_value = fake_filename

        request = DownloadRequest(url="https://www.youtube.com/watch?v=vid123", output_dir=tmp_path)
        result = download_video(request)

    assert result.success is True
    assert result.error is None


def test_instagram_download_uses_ytdlp_and_succeeds(tmp_path):
    fake_info = {"uploader": "someone", "id": "reel123", "ext": "mp4"}
    fake_filename = str(tmp_path / "someone_reel123.mp4")

    with patch("tikpull.downloader.yt_dlp.YoutubeDL") as mock_ydl_cls:
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = fake_info
        mock_ydl.prepare_filename.return_value = fake_filename

        request = DownloadRequest(
            url="https://www.instagram.com/reel/reel123/", output_dir=tmp_path
        )
        result = download_video(request)

    assert result.success is True
    assert result.error is None


def test_youtube_failure_does_not_fall_back_to_tikwm(tmp_path):
    """A failed YouTube download must not trigger the TikTok-only tikwm API."""
    with (
        patch("tikpull.downloader.yt_dlp.YoutubeDL") as mock_ydl_cls,
        patch("tikpull.downloader.httpx.post") as mock_post,
    ):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.side_effect = yt_dlp.utils.DownloadError("video unavailable")

        request = DownloadRequest(
            url="https://www.youtube.com/watch?v=missing", output_dir=tmp_path
        )
        result = download_video(request)

    assert result.success is False
    mock_post.assert_not_called()


def test_tiktok_failure_still_falls_back_to_tikwm(tmp_path):
    """Existing TikTok behavior is preserved: yt-dlp failure -> tikwm fallback."""
    with (
        patch("tikpull.downloader.yt_dlp.YoutubeDL") as mock_ydl_cls,
        patch("tikpull.downloader.httpx.post") as mock_post,
    ):
        mock_ydl = MagicMock()
        mock_ydl_cls.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.side_effect = yt_dlp.utils.DownloadError("boom")

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {}}
        mock_post.return_value = mock_response

        request = DownloadRequest(url="https://www.tiktok.com/@user/video/123", output_dir=tmp_path)
        download_video(request)

    mock_post.assert_called_once()
