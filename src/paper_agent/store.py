import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "papertrail.sqlite3"
        with self.connection() as conn:
            conn.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS papers (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, kind TEXT NOT NULL,
                    source_url TEXT NOT NULL, pages INTEGER NOT NULL,
                    created_at TEXT NOT NULL, warning TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY, paper_id TEXT NOT NULL REFERENCES papers(id),
                    page INTEGER NOT NULL, text TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS chunks_paper ON chunks(paper_id);
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY, cache_key TEXT NOT NULL, status TEXT NOT NULL,
                    payload TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS job_cache ON jobs(cache_key,status);
            """)
            # A restarted process cannot resume a model call in a dead worker.
            conn.execute(
                "UPDATE jobs SET status='failed', payload=? WHERE status IN ('queued','running')",
                (json.dumps({"error": "Server restarted. Please run the analysis again."}),),
            )

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def add_paper(self, paper, chunks):
        with self.connection() as conn:
            existing = conn.execute("SELECT * FROM papers WHERE id=?", (paper["id"],)).fetchone()
            if existing:
                return dict(existing), True
            conn.execute(
                "INSERT INTO papers VALUES (?,?,?,?,?,?,?)",
                tuple(
                    paper[k]
                    for k in ("id", "title", "kind", "source_url", "pages", "created_at", "warning")
                ),
            )
            conn.executemany(
                "INSERT INTO chunks VALUES (?,?,?,?)",
                [(c["id"], paper["id"], c["page"], c["text"]) for c in chunks],
            )
        return paper, False

    def papers(self):
        with self.connection() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM papers ORDER BY created_at DESC")]

    def get_papers(self, ids):
        by_id = {p["id"]: p for p in self.papers()}
        if len(set(ids)) != len(ids) or any(i not in by_id for i in ids):
            raise ValueError("Choose distinct papers that exist in this library")
        return [by_id[i] for i in ids]

    def chunks(self, ids):
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        with self.connection() as conn:
            return [
                dict(r)
                for r in conn.execute(
                    f"SELECT c.*,p.title,p.kind FROM chunks c JOIN papers p ON p.id=c.paper_id "
                    f"WHERE paper_id IN ({placeholders}) ORDER BY paper_id,page,c.id",
                    ids,
                )
            ]

    def save_job(self, job_id, cache_key, status, payload):
        with self.connection() as conn:
            conn.execute(
                "INSERT INTO jobs VALUES (?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET "
                "status=excluded.status,payload=excluded.payload",
                (job_id, cache_key, status, json.dumps(payload), now()),
            )

    def job(self, job_id):
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            return None
        return {**dict(row), "payload": json.loads(row["payload"])}

    def cached(self, key):
        with self.connection() as conn:
            row = conn.execute(
                "SELECT id FROM jobs WHERE cache_key=? AND status='complete' "
                "ORDER BY created_at DESC LIMIT 1",
                (key,),
            ).fetchone()
        return self.job(row["id"]) if row else None
