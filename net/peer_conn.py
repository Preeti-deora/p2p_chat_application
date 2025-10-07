#!/usr/bin/env python3
from __future__ import annotations
import queue
import socket
import threading
from typing import Callable, Optional

def _make_line_protocol():
    buf = bytearray()
    lock = threading.Lock()

    def feed(data: bytes):
        out = []
        with lock:
            buf.extend(data)
            while True:
                i = buf.find(b"\n")
                if i == -1:
                    break
                line = buf[:i]
                del buf[:i+1]
                try:
                    out.append(line.decode("utf-8", errors="replace"))
                except Exception:
                    out.append("<decode error>")
        return out

    def encode(msg: str) -> bytes:
        return (msg + "\n").encode("utf-8")

    return feed, encode


class PeerConn:
    """A single chat connection with queue-based delivery for UI threads."""
    def __init__(self, ui_callback: Callable[[str], None]):
        self._sock: Optional[socket.socket] = None
        self._stop_evt = threading.Event()
        self._recv_q: "queue.Queue[str]" = queue.Queue()
        self._ui_callback = ui_callback
        self._feed, self._encode = _make_line_protocol()
        self._reader_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    # ---------------- utils ----------------
    def _enable_keepalive(self, s: socket.socket):
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        except OSError:
            pass  # not critical

    def is_connected(self) -> bool:
        return isinstance(self._sock, socket.socket)

    # ------------- connect / adopt -------------
    def connect(self, host: str, port: int) -> bool:
        self.close()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        try:
            s.connect((host, port))
        except Exception as e:
            self._recv_q.put(f"[error] Could not connect: {e}")
            try: s.close()
            except Exception: pass
            return False

        s.settimeout(None)  # blocking
        self._enable_keepalive(s)

        with self._lock:
            self._sock = s
            self._stop_evt.clear()
            self._reader_thread = threading.Thread(target=self._reader, args=(s,), daemon=True)
            self._reader_thread.start()

        self._recv_q.put(f"[system] Connected to {host}:{port}")
        return True

    def adopt(self, sock: socket.socket, addr) -> None:
        self.close()
        try: sock.settimeout(None)
        except Exception: pass
        self._enable_keepalive(sock)

        with self._lock:
            self._sock = sock
            self._stop_evt.clear()
            self._reader_thread = threading.Thread(target=self._reader, args=(sock,), daemon=True)
            self._reader_thread.start()

        self._recv_q.put(f"[system] Incoming connection from {addr[0]}:{addr[1]}")

    # ---------------- reader ----------------
    def _reader(self, conn: socket.socket) -> None:
        """
        Blocking recv loop; only exits when:
        - peer cleanly closes (recv() == b"")
        - a real socket error occurs
        - stop event is set from close()
        """
        try:
            conn.settimeout(0.6)  # short timeout to allow graceful stop polling
            while not self._stop_evt.is_set():
                try:
                    data = conn.recv(4096)
                except socket.timeout:
                    continue  # keep waiting
                except OSError as e:
                    self._recv_q.put(f"[error] recv failed: {e}")
                    break

                if not data:
                    # peer closed
                    self._recv_q.put("[system] Peer closed the connection.")
                    break

                for line in self._feed(data):
                    self._recv_q.put(line)
        except Exception as e:
            self._recv_q.put(f"[error] {e}")
        finally:
            # mark disconnected exactly once
            self._recv_q.put("[system] Disconnected.")
            self._safe_close()

    # ---------------- send / poll ----------------
    def send(self, msg: str) -> None:
        if not isinstance(self._sock, socket.socket):
            self._recv_q.put("[error] Not connected.")
            return
        try:
            self._sock.sendall(self._encode(msg))
        except Exception as e:
            # surface the error and close; UI will see it
            self._recv_q.put(f"[error] send failed: {e}")
            self._safe_close()

    def poll_recv(self) -> None:
        try:
            while True:
                line = self._recv_q.get_nowait()
                self._ui_callback(line)
        except queue.Empty:
            pass

    # ---------------- close ----------------
    def _safe_close(self):
        """Internal: close without re-entrancy problems."""
        with self._lock:
            if isinstance(self._sock, socket.socket):
                try:
                    # avoid SHUT_RDWR on half-closed sockets on macOS that may raise
                    self._sock.close()
                except Exception:
                    pass
            self._sock = None
            self._stop_evt.set()

    def close(self) -> None:
        self._safe_close()
