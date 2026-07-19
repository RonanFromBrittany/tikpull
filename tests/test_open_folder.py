"""Tests for the /api/open-folder route."""

import asyncio
import sys
from unittest.mock import patch

import pytest

from tikpull.web.routes import _open_in_file_manager, open_folder


def test_open_folder_returns_output_dir(tmp_path):
    output_dir = tmp_path / "downloads"
    fake_config = {"output_dir": str(output_dir)}

    with (
        patch("tikpull.web.routes.load_config", return_value=fake_config),
        patch("tikpull.web.routes._open_in_file_manager") as mock_open,
    ):
        result = asyncio.run(open_folder())

    assert result["status"] == "opened"
    assert result["path"] == str(output_dir.resolve())
    assert output_dir.is_dir()  # created if missing
    mock_open.assert_called_once()


@pytest.mark.parametrize(
    ("platform", "expected_cmd"),
    [
        ("darwin", "open"),
        ("win32", "explorer"),
        ("linux", "xdg-open"),
    ],
)
def test_open_in_file_manager_picks_platform_command(tmp_path, platform, expected_cmd):
    with (
        patch.object(sys, "platform", platform),
        patch("tikpull.web.routes.subprocess.Popen") as mock_popen,
    ):
        _open_in_file_manager(tmp_path)

    mock_popen.assert_called_once_with([expected_cmd, str(tmp_path)])


def test_open_folder_raises_http_exception_on_failure(tmp_path):
    from fastapi import HTTPException

    fake_config = {"output_dir": str(tmp_path)}

    with (
        patch("tikpull.web.routes.load_config", return_value=fake_config),
        patch(
            "tikpull.web.routes._open_in_file_manager",
            side_effect=OSError("no file manager"),
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(open_folder())

    assert exc_info.value.status_code == 500
    assert "no file manager" in exc_info.value.detail
