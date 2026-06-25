"""
history.py
----------
Persists every /solve run so the frontend can show a history panel, an
aggregate stats dashboard (success rate per problem, average attempts),
and shareable permalinks to a specific result (GET /result/{id}).

Separate SQLite file from skill_library.py on purpose — different access
patterns (this is append-mostly + occasional lookup by ID; skill_library
does similarity search) and keeping them apart makes each easier to reason
about independently.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "nexus_history.db"


@dataclass
class SolveRecord:
    id: str
    problem_id: str
    success: bool
    attempts_count: int
    elapsed_seconds: float
    reward: float
    llm_provider: str
    created_at: float


class HistoryStore:
    def __init__(self, db_path: Path = DB_PATH):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS solve_records (
                id TEXT PRIMARY KEY,
                problem_id TEXT NOT NULL,
                success INTEGER NOT NULL,
                attempts_count INTEGER NOT NULL,
                elapsed_seconds REAL NOT NULL,
                reward REAL NOT NULL,
                llm_provider TEXT NOT NULL,
                full_result_json TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_created_at ON solve_records(created_at DESC)"
        )
        self._conn.commit()

    def store(self, problem_id: str, success: bool, attempts_count: int,
              elapsed_seconds: float, reward: float, llm_provider: str,
              full_result: dict[str, Any]) -> str:
        record_id = str(uuid.uuid4())
        self._conn.execute(
            """INSERT INTO solve_records
               (id, problem_id, success, attempts_count, elapsed_seconds,
                reward, llm_provider, full_result_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (record_id, problem_id, int(success), attempts_count, elapsed_seconds,
             reward, llm_provider, json.dumps(full_result), time.time()),
        )
        self._conn.commit()
        return record_id

    def get_full_result(self, record_id: str) -> dict[str, Any] | None:
        cur = self._conn.execute(
            "SELECT full_result_json FROM solve_records WHERE id = ?", (record_id,)
        )
        row = cur.fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        cur = self._conn.execute(
            """SELECT id, problem_id, success, attempts_count, elapsed_seconds,
                      reward, llm_provider, created_at
               FROM solve_records ORDER BY created_at DESC LIMIT ?""",
            (limit,),
        )
        cols = [d[0] for d in cur.description]
        return [
            {**dict(zip(cols, row)), "success": bool(row[cols.index("success")])}
            for row in cur.fetchall()
        ]

    def aggregate_stats(self) -> dict[str, Any]:
        cur = self._conn.execute(
            """SELECT problem_id,
                      COUNT(*) as total,
                      SUM(success) as successes,
                      AVG(attempts_count) as avg_attempts,
                      AVG(elapsed_seconds) as avg_elapsed
               FROM solve_records GROUP BY problem_id"""
        )
        per_problem = {}
        total_solves = 0
        total_successes = 0
        for problem_id, total, successes, avg_attempts, avg_elapsed in cur.fetchall():
            per_problem[problem_id] = {
                "total_solves": total,
                "success_rate": round((successes or 0) / total, 3) if total else 0.0,
                "avg_attempts": round(avg_attempts, 2) if avg_attempts else None,
                "avg_elapsed_seconds": round(avg_elapsed, 2) if avg_elapsed else None,
            }
            total_solves += total
            total_successes += successes or 0
        return {
            "total_solves": total_solves,
            "overall_success_rate": round(total_successes / total_solves, 3) if total_solves else 0.0,
            "per_problem": per_problem,
        }

    def close(self) -> None:
        self._conn.close()
