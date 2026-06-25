"""
skill_library.py
-----------------
NEXUS's memory: every time a bug gets fixed, the (problem, buggy_code,
violated_constraint, fix) pattern is stored. Future generation attempts
retrieve the most similar past bugs and inject them as few-shot context,
so the system avoids repeating mistakes it has already learned to fix.

Deliberately lightweight for free-tier deployment: similarity search uses
TF-IDF + cosine similarity (scikit-learn) over a SQLite-backed store rather
than a heavyweight sentence-transformer + vector-DB stack. TF-IDF on short,
code-shaped text (constraint names, error messages, short code snippets) is
a perfectly reasonable retrieval signal here, costs ~0 RAM beyond scikit-
learn itself, and needs no GPU and no external embedding API — which matters
because this whole project is designed to run on Render's free tier.
"""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, asdict
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "nexus_skills.db"
MIN_REWARD_TO_STORE = 0.3


@dataclass
class BugFixPair:
    problem_id: str
    bug_type: str
    buggy_code: str
    violated_constraint: str
    fix_explanation: str
    fixed_code: str
    reward: float
    created_at: float = 0.0


class SkillLibrary:
    def __init__(self, db_path: Path = DB_PATH):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._init_schema()

    def _init_schema(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS bug_fix_pairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_id TEXT NOT NULL,
                bug_type TEXT NOT NULL,
                buggy_code TEXT NOT NULL,
                violated_constraint TEXT NOT NULL,
                fix_explanation TEXT NOT NULL,
                fixed_code TEXT NOT NULL,
                reward REAL NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        self._conn.commit()

    def store(self, pair: BugFixPair) -> bool:
        if pair.reward < MIN_REWARD_TO_STORE:
            return False
        self._conn.execute(
            """INSERT INTO bug_fix_pairs
               (problem_id, bug_type, buggy_code, violated_constraint,
                fix_explanation, fixed_code, reward, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (pair.problem_id, pair.bug_type, pair.buggy_code, pair.violated_constraint,
             pair.fix_explanation, pair.fixed_code, pair.reward, time.time()),
        )
        self._conn.commit()
        return True

    def count(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) FROM bug_fix_pairs")
        return cur.fetchone()[0]

    def _all_rows(self, problem_id: str | None = None) -> list[dict]:
        if problem_id:
            cur = self._conn.execute(
                "SELECT * FROM bug_fix_pairs WHERE problem_id = ?", (problem_id,)
            )
        else:
            cur = self._conn.execute("SELECT * FROM bug_fix_pairs")
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]

    def retrieve_similar(self, query_text: str, problem_id: str | None = None, k: int = 3) -> list[dict]:
        """
        TF-IDF + cosine similarity retrieval over stored (bug, fix) docs.
        Scoped to the same problem_id by default since a fix learned for
        sorting bugs is rarely a useful few-shot example for a two_sum bug.
        """
        rows = self._all_rows(problem_id=problem_id)
        if not rows:
            return []

        corpus = [
            f"{r['bug_type']} {r['violated_constraint']} {r['buggy_code'][:300]}"
            for r in rows
        ]
        corpus.append(query_text)

        try:
            vectorizer = TfidfVectorizer(stop_words="english", max_features=2000)
            tfidf = vectorizer.fit_transform(corpus)
        except ValueError:
            # Happens if corpus is degenerate (e.g. all-empty strings); fail soft.
            return rows[:k]

        query_vec = tfidf[-1]
        doc_vecs = tfidf[:-1]
        sims = cosine_similarity(query_vec, doc_vecs)[0]

        ranked = sorted(zip(rows, sims), key=lambda x: x[1], reverse=True)
        return [r for r, score in ranked[:k] if score > 0.0]

    def build_few_shot_context(self, query_text: str, problem_id: str | None = None, k: int = 2) -> str:
        similar = self.retrieve_similar(query_text, problem_id=problem_id, k=k)
        if not similar:
            return ""
        blocks = []
        for r in similar:
            blocks.append(
                f"Past bug ({r['bug_type']}): violated `{r['violated_constraint']}`.\n"
                f"Fix that worked: {r['fix_explanation']}"
            )
        return "RELEVANT PAST FIXES (from NEXUS's memory of similar bugs):\n" + "\n\n".join(blocks)

    def stats(self) -> dict:
        rows = self._all_rows()
        by_type: dict[str, int] = {}
        for r in rows:
            by_type[r["bug_type"]] = by_type.get(r["bug_type"], 0) + 1
        return {"total_patterns": len(rows), "by_bug_type": by_type}

    def close(self) -> None:
        """Explicitly close the underlying SQLite connection. Needed before
        deleting the backing file on Windows, where an open file handle
        blocks deletion (unlike POSIX, which allows unlinking an open file)."""
        self._conn.close()
