#!/usr/bin/env python3
"""
UDP LAN presence beacons (no central server).
Each app instance:
- broadcasts {"name": <display_name>, "port": <tcp_port>} every BCAST_INTERVAL
- listens on BCAST_PORT and keeps a TTL-filtered list of peers.

Multiple processes can bind the same UDP port via SO_REUSEADDR (and SO_REUSEPORT when available).
"""

from __future__ import annotations
import json
import socket
import threading
import time
from typing import Dict, List, Tuple

BCAST_PORT = 54545          # shared UDP discovery port
BCAST_INTERVAL = 2.5        # seconds between beacons
PEER_TTL = 8.0              # seconds until peer considered offline


class Presence:
    def __init__(self, name: str, tcp_port: int):
        self.name = name
        self.tcp_port = tcp_port

        self._running = threading.Event()
        self._running.set()

        self._lock = threading.Lock()
        # key: (ip, port) -> {"name": str, "ip": str, "port": int, "last_seen": float}
        self._peers: Dict[Tuple[str, int], Dict] = {}

        self._th_bcast = threading.Thread(target=self._broadcaster, daemon=True)
        self._th_recv = threading.Thread(target=self._receiver, daemon=True)

    # ---- lifecycle ----
    def start(self) -> None:
        self._th_bcast.start()
        self._th_recv.start()

    def stop(self) -> None:
        self._running.clear()

    # ---- internals ----
    def _broadcaster(self) -> None:
        """Send presence beacons to the local subnet."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        payload = {"name": self.name, "port": self.tcp_port}
        while self._running.is_set():
            try:
                msg = json.dumps(payload).encode("utf-8")
                sock.sendto(msg, ("255.255.255.255", BCAST_PORT))
            except Exception:
                # Ignore transient network errors
                pass
            time.sleep(BCAST_INTERVAL)

    def _receiver(self) -> None:
        """Receive beacons, update the in-memory peer map."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            # Not available on some platforms; best effort.
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except (AttributeError, OSError):
            pass

        sock.bind(("", BCAST_PORT))
        sock.settimeout(0.5)

        while self._running.is_set():
            try:
                data, (ip, _port) = sock.recvfrom(2048)
            except socket.timeout:
                continue
            except Exception:
                break

            try:
                info = json.loads(data.decode("utf-8", errors="replace"))
                peer_name = (info.get("name") or "").strip() or "Unknown"
                peer_port = int(info.get("port") or 0)
                if peer_port <= 0:
                    continue
                # Ignore our own packets (same name + port)
                if peer_name == self.name and peer_port == self.tcp_port:
                    continue

                key = (ip, peer_port)
                now = time.time()
                with self._lock:
                    self._peers[key] = {
                        "name": peer_name,
                        "ip": ip,
                        "port": peer_port,
                        "last_seen": now,
                    }
            except Exception:
                # Malformed JSON or other error — ignore
                continue

    # ---- API ----
    def get_active_peers(self) -> List[Dict]:
        """Return sorted list of peers filtered by TTL."""
        now = time.time()
        with self._lock:
            expired = [k for k, v in self._peers.items() if now - v["last_seen"] > PEER_TTL]
            for k in expired:
                del self._peers[k]
            items = list(self._peers.values())
        items.sort(key=lambda x: (x["name"].lower(), x["ip"], x["port"]))
        return items
