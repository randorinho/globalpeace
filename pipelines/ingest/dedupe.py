"""Local content-hash dedupe so re-runs don't re-post the same item.

Scaffold-stage: a sqlite ledger next to the pipeline. Server-side dedupe
(unique source_url index at the origin) should complement this later.
"""
import hashlib
import sqlite3
from pathlib import Path

STATE_DIR = Path(__file__).parent.parent / ".state"


class SeenLedger:
    def __init__(self, path: Path | None = None):
        STATE_DIR.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(path or STATE_DIR / "seen.db")
        self.conn.execute("CREATE TABLE IF NOT EXISTS seen (h TEXT PRIMARY KEY, url TEXT, ts TEXT DEFAULT CURRENT_TIMESTAMP)")

    @staticmethod
    def key(url: str, title: str) -> str:
        return hashlib.sha256(f"{url}|{title}".encode()).hexdigest()

    def is_seen(self, url: str, title: str) -> bool:
        h = self.key(url, title)
        return self.conn.execute("SELECT 1 FROM seen WHERE h=?", (h,)).fetchone() is not None

    def mark(self, url: str, title: str) -> None:
        self.conn.execute("INSERT OR IGNORE INTO seen (h, url) VALUES (?, ?)", (self.key(url, title), url))
        self.conn.commit()
