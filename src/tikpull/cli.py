"""Command-line interface for tikpull."""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .config import get_cookies_file, get_output_dir, load_config
from .downloader import download_video
from .models import DownloadRequest, DownloadResult

console = Console()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="tikpull",
        description="Download TikTok, YouTube, and Instagram videos from the command line.",
    )
    parser.add_argument(
        "urls", nargs="*", help="One or more video URLs (TikTok, YouTube, Instagram, ...)"
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        metavar="DIR",
        help="Output directory (overrides config file)",
    )
    parser.add_argument(
        "-f",
        "--file",
        metavar="FILE",
        help="Text file containing one URL per line (batch mode)",
    )
    parser.add_argument("--version", action="version", version="tikpull 0.3.0")
    return parser.parse_args(argv)


def _read_url_file(path: Path) -> tuple[list[str], list[str]]:
    """Read a URL file and return (active_urls, original_lines).

    Lines starting with '#' or empty lines are ignored.
    original_lines preserves the full file content for rewriting.
    """
    lines = path.read_text().splitlines()
    active_urls = [
        line.strip() for line in lines if line.strip() and not line.strip().startswith("#")
    ]
    return active_urls, lines


def _comment_url_in_file(path: Path, url: str, original_lines: list[str]) -> None:
    """Comment out the line matching url in the file.

    Rewrites the file in place, preserving all other lines unchanged.
    """
    new_lines = []
    for line in original_lines:
        if line.strip() == url:
            new_lines.append(f"# {line}")
        else:
            new_lines.append(line)
    path.write_text("\n".join(new_lines) + "\n")


def _collect_urls(args: argparse.Namespace) -> tuple[list[str], Path | None, list[str]]:
    """Collect URLs from CLI args and/or file.

    Returns (urls, url_file_path, original_lines).
    url_file_path and original_lines are None/[] if no file was provided.
    """
    urls = list(args.urls)
    url_file: Path | None = None
    original_lines: list[str] = []

    if args.file:
        url_file = Path(args.file)
        if not url_file.is_file():
            console.print(f"[red]Error:[/red] file not found: {args.file}")
            sys.exit(1)
        file_urls, original_lines = _read_url_file(url_file)
        urls.extend(file_urls)

    return urls, url_file, original_lines


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    urls, url_file, original_lines = _collect_urls(args)

    if not urls:
        console.print("[yellow]No URLs provided. Use --help for usage.[/yellow]")
        sys.exit(0)

    config = load_config()
    output_dir = get_output_dir(config, cli_override=args.output)
    cookies_file = get_cookies_file(config)
    console.print(f"[dim]Output directory: {output_dir}[/dim]")

    results: list[DownloadResult] = []

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        for url in urls:
            task = progress.add_task(f"Downloading {url[:60]}…", total=None)
            request = DownloadRequest(url=url, output_dir=output_dir, cookies_file=cookies_file)
            result = download_video(request)
            results.append(result)
            progress.remove_task(task)

            # Comment out the URL in the file immediately after a successful download
            if result.success and url_file is not None:
                _comment_url_in_file(url_file, url, original_lines)
                # Keep original_lines in sync with the rewritten file
                original_lines = url_file.read_text().splitlines()

    # Summary table
    table = Table(title="Download results", show_lines=True)
    table.add_column("URL", style="cyan", max_width=50)
    table.add_column("Status", justify="center")
    table.add_column("Output / Error")

    for r in results:
        if r.success:
            table.add_row(r.url, "[green]✓[/green]", str(r.output_path))
        else:
            table.add_row(r.url, "[red]✗[/red]", r.error or "Unknown error")

    console.print(table)

    failed = sum(1 for r in results if not r.success)
    sys.exit(1 if failed else 0)
