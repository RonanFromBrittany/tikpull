"""Configuration management for tikpull."""

from pathlib import Path

try:
    import tomllib  # stdlib from Python 3.11+
except ImportError:
    import tomli as tomllib  # fallback for older Python

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "tikpull" / "config.toml"
DEFAULT_OUTPUT_DIR = Path.home() / "Downloads" / "tikpull"


def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> dict:
    """Load configuration from a TOML file.

    Returns an empty dict if the file does not exist.
    """
    if not config_path.is_file():
        return {}
    with config_path.open("rb") as f:
        return tomllib.load(f)


def get_output_dir(config: dict, cli_override: str | None = None) -> Path:
    """Resolve the output directory with the following priority:
    1. CLI argument (-o / --output)
    2. config.toml output_dir
    3. ~/Downloads/tikpull (fallback)

    The fallback used to be the current working directory, but that's
    unpredictable for a GUI app (desktop launch) where the cwd isn't under
    the user's control, so a fixed, discoverable default is used instead.
    """
    if cli_override is not None:
        return Path(cli_override).expanduser().resolve()
    if "output_dir" in config:
        return Path(config["output_dir"]).expanduser().resolve()
    return DEFAULT_OUTPUT_DIR


def get_url_file(config: dict) -> Path | None:
    """Return the default URL file path from config, or None if not set."""
    if "url_file" in config:
        path = Path(config["url_file"]).expanduser().resolve()
        return path if path.is_file() else None
    return None
