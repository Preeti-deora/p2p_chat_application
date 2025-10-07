# storage.py
import json
import os
import threading
import time
from pathlib import Path

def _now_ts() -> float:
    return time.time()

def _peer_key(name: str, ip: str, port: int) -> str:
    return f"{name}@{ip}:{port}"

class Storage:
    """
    Very small local JSON storage for:
      - friends (people you've chatted with)
      - messages (per peer)
    File lives in: ~/.p2p_desktop_app/state.json
    """
    def __init__(self, path: str | None = None):
        if path is None:
            base = Path(os.path.expanduser("~")) / ".p2p_desktop_app"
            base.mkdir(parents=True, exist_ok=True)
            path = str(base / "state.json")
        self.path = path
        self._lock = threading.Lock()
        self._data = {"friends": {}, "messages": {}}  # keys are peer_key

        self._load()

    # ---------- low-level ----------
    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            # sanity
            self._data.setdefault("friends", {})
            self._data.setdefault("messages", {})
        except FileNotFoundError:
            self._save()
        except Exception:
            # if corrupt, back it up and start fresh
            try:
                bak = self.path + ".bak"
                os.replace(self.path, bak)
            except Exception:
                pass
            self._data = {"friends": {}, "messages": {}}
            self._save()

    def _save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)

    # ---------- friends ----------
    def upsert_friend(self, name: str, ip: str, port: int):
        """
        Add/update a friend (someone you've chatted with).
        """
        key = _peer_key(name, ip, port)
        with self._lock:
            self._data["friends"][key] = {
                "name": name,
                "ip": ip,
                "port": int(port),
                "last_spoke": _now_ts(),
            }
            self._save()
        return key

    def get_friends(self) -> list[dict]:
        """
        Returns a list of friend dicts sorted by last_spoke desc.
        """
        with self._lock:
            friends = list(self._data["friends"].values())
        friends.sort(key=lambda x: x.get("last_spoke", 0), reverse=True)
        return friends

    # ---------- messages ----------
    def add_message(self, peer_key: str, role: str, text: str, ts: float | None = None):
        """
        Append a message to a peer's history.
        role: "me" or "peer"
        """
        if ts is None:
            ts = _now_ts()
        item = {"role": role, "text": text, "ts": ts}
        with self._lock:
            self._data["messages"].setdefault(peer_key, [])
            self._data["messages"][peer_key].append(item)
            self._save()

    def get_messages(self, peer_key: str, limit: int = 200) -> list[dict]:
        with self._lock:
            msgs = list(self._data["messages"].get(peer_key, []))
        if limit and len(msgs) > limit:
            return msgs[-limit:]
        return msgs

    # ---------- helpers for callers ----------
    @staticmethod
    def make_peer_key(name: str, ip: str, port: int) -> str:
        return _peer_key(name, ip, port)
