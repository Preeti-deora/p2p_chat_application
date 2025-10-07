#!/usr/bin/env python3
"""
TCP inbound listener.
- Binds to host/port (port=0 to auto-pick a free port).
- Accepts connections and hands (conn, addr) off to a UI callback on the main thread via queue.
"""

from __future__ import annotations
import socket
import threading
from typing import Callable, Optional

TCP_BACKLOG = 10


class InboxServer:
    """
    on_incoming: callback(conn: socket.socket, addr: (str, int))
                 UI code typically enqueues this and opens a ChatWindow that adopts the socket.
    """
    def __init__(self, on_incoming: Callable[[socket.socket, tuple], None]):
        self.on_incoming = on_incoming
        self._server: Optional[socket.socket] = None
        self._running = threading.Event()
        self._th: Optional[threading.Thread] = None

    def start(self, host: str = "0.0.0.0", port: int = 0) -> int:
        """Start listener; returns the actual bound port (useful when port=0)."""
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))  # port=0 => OS chooses a free port
        srv.listen(TCP_BACKLOG)

        self._server = srv
        self._running.set()
        self._th = threading.Thread(target=self._acceptor, daemon=True)
        self._th.start()
        return srv.getsockname()[1]

    def _acceptor(self) -> None:
        while self._running.is_set():
            try:
                conn, addr = self._server.accept()
            except OSError:
                break
            # hand off for UI to open a window
            try:
                self.on_incoming(conn, addr)
            except Exception:
                # If UI callback crashes we must close the socket to avoid leaks.
                try:
                    conn.close()
                except Exception:
                    pass

    def stop(self) -> None:
        self._running.clear()
        if isinstance(self._server, socket.socket):
            try:
                self._server.close()
            except Exception:
                pass
        self._server = None
