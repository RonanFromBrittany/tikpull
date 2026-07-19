"""Tests for the desktop launcher's helper functions.

These tests deliberately avoid importing `webview` (the desktop extra), so
they run on CI without the desktop dependency installed. Only `main()`
imports `webview`, and it does so lazily inside the function body.
"""

import socket

import pytest

from tikpull.desktop import find_free_port, wait_until_ready


def test_find_free_port_returns_an_unbound_port():
    port = find_free_port(start=9500)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # Binding should succeed since the port was reported as free.
        sock.bind(("127.0.0.1", port))


def test_find_free_port_skips_a_port_already_in_use():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as blocker:
        blocker.bind(("127.0.0.1", 0))
        blocker.listen(1)
        busy_port = blocker.getsockname()[1]

        found = find_free_port(start=busy_port)

    assert found != busy_port


def test_wait_until_ready_returns_once_port_is_listening():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.bind(("127.0.0.1", 0))
        server_sock.listen(1)
        port = server_sock.getsockname()[1]

        wait_until_ready(port, timeout=2.0)  # should return without raising


def test_wait_until_ready_times_out_if_nothing_listens():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        free_port = sock.getsockname()[1]
    # free_port is now closed and nothing else is listening on it

    with pytest.raises(TimeoutError):
        wait_until_ready(free_port, timeout=0.3, interval=0.05)
