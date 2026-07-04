"""Command-line interface for tikpull."""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .downloader import download_batch, download_video
from .models import DownloadRequest

console = Console()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="tikpull",
        description="Download TikTok videos from the command line.",
    )
    parser.add_argument("urls", nargs="*", help="One or more TikTok video URLs")
    parser.add_argument(
        "-o", "--output", default=".", metavar="DIR",
        help="Output directory (default: current directory)",
    )
    parser.add_argument(
        "-f", "--file", metavar="FILE",
        help="Text file containing one URL per line (batch mode)",
    )
    parser.add_argument("--version", action="version", version="tikpull 0.1.0")
    return parser.parse_args(argv)


def _collect_urls(args: argparse.Namespace) -> list[str]:
    urls = list(args.urls)
    if args.file:
        path = Path(args.file)
        if not path.is_file():
            console.print(f"[red]Error:[/red] file not found: {args.file}")
            sys.exit(1)
        lines = path.read_text().splitlines()
        urls.extend(line.strip() for line in lines if line.strip())
    return urls


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    urls = _collect_urls(args)

    if not urls:
        console.print("[yellow]No URLs provided. Use --help for usage.[/yellow]")
        sys.exit(0)

    output_dir = Path(args.output)
    requests = [DownloadRequest(url=url, output_dir=output_dir) for url in urls]

    results = []
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        for req in requests:
            task = progress.add_task(f"Downloading {req.url[:60]}…", total=None)
            result = download_video(req)
            results.append(result)
            progress.remove_task(task)

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
