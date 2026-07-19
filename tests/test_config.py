"""Tests for output directory resolution."""

from pathlib import Path

from tikpull.config import DEFAULT_OUTPUT_DIR, get_output_dir


def test_cli_override_wins_over_everything():
    config = {"output_dir": "/some/configured/path"}
    result = get_output_dir(config, cli_override="/cli/path")
    assert result == Path("/cli/path").resolve()


def test_config_output_dir_used_when_no_cli_override():
    config = {"output_dir": "~/some/configured/path"}
    result = get_output_dir(config)
    assert result == Path("~/some/configured/path").expanduser().resolve()


def test_falls_back_to_downloads_tikpull_when_unset():
    result = get_output_dir({})
    assert result == DEFAULT_OUTPUT_DIR
    assert result == Path.home() / "Downloads" / "tikpull"
