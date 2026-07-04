from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DownloadRequest:
    """Represents a single video download request."""

    url: str
    output_dir: Path = field(default_factory=lambda: Path("."))
    filename: str | None = None  # None = auto-generated from metadata


@dataclass
class DownloadResult:
    """Outcome of a single video download attempt."""

    url: str
    success: bool
    output_path: Path | None = None
    error: str | None = None
