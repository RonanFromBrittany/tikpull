"""Desktop entry point for tikpull.

Runs the FastAPI web server in a background thread and displays it inside a
native window (via pywebview), so tikpull behaves like a regular desktop app
instead of requiring a terminal + browser tab.

Requires the `desktop` extra:

    pip install "tikpull[desktop]"
"""

from __future__ import annotations

import socket
import threading
import time

import uvicorn

from tikpull.web.app import app

HOST = "127.0.0.1"
WINDOW_TITLE = "tikpull"
WINDOW_WIDTH = 860
WINDOW_HEIGHT = 900
MIN_WINDOW_SIZE = (600, 500)


def find_free_port(start: int = 8080, attempts: int = 50) -> int:
    """Return the first TCP port at or after `start` that isn't already in use."""
    port = start
    for _ in range(attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((HOST, port)) != 0:
                return port
        port += 1
    raise RuntimeError(f"No free port found in range [{start}, {start + attempts})")


def wait_until_ready(port: int, timeout: float = 10.0, interval: float = 0.1) -> None:
    """Block until something is listening on `port`, or raise TimeoutError."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((HOST, port)) == 0:
                return
        time.sleep(interval)
    raise TimeoutError(f"tikpull server did not start on port {port} within {timeout}s")


def run_server(port: int) -> None:
    """Run the FastAPI app with uvicorn. Blocking call — meant for a background thread."""
    config = uvicorn.Config(app, host=HOST, port=port, log_level="warning")
    uvicorn.Server(config).run()


def main() -> None:
    """Launch tikpull in a native desktop window."""
    try:
        import webview
    except ImportError as exc:
        raise SystemExit(
            "The desktop UI requires the 'desktop' extra.\n"
            'Install it with: pip install "tikpull[desktop]"'
        ) from exc

    class Api:
        """Methods exposed to the frontend as window.pywebview.api.<name>().

        Lets the Settings page offer native folder/file pickers instead of
        requiring the user to type an exact path — a web page can't expose
        real filesystem paths, but the pywebview desktop window can.
        """

        def choose_folder(self) -> str | None:
            result = webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
            return result[0] if result else None

        def choose_file(self) -> str | None:
            result = webview.windows[0].create_file_dialog(webview.OPEN_DIALOG)
            return result[0] if result else None

    port = find_free_port()
    server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    server_thread.start()
    wait_until_ready(port)

    webview.create_window(
        WINDOW_TITLE,
        f"http://{HOST}:{port}",
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=MIN_WINDOW_SIZE,
        js_api=Api(),
    )
    webview.start()


if __name__ == "__main__":
    main()
