import json
import os
import sqlite3
import time
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from app.settings import settings


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    _ensure_parent_dir(settings.audit_db_path)
    conn = sqlite3.connect(settings.audit_db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ingest_events (
            id TEXT PRIMARY KEY,
            ts_unix REAL NOT NULL,
            actor_role TEXT NOT NULL,
            folder_path TEXT NOT NULL,
            file_count INTEGER NOT NULL,
            chunk_count INTEGER NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS query_events (
            id TEXT PRIMARY KEY,
            ts_unix REAL NOT NULL,
            actor_role TEXT NOT NULL,
            question TEXT NOT NULL,
            question_redacted TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            escalation_ticket_id TEXT,
            retrieved_k INTEGER NOT NULL,
            sources_json TEXT NOT NULL,
            answer TEXT,
            answer_redacted TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS escalation_tickets (
            id TEXT PRIMARY KEY,
            ts_unix REAL NOT NULL,
            actor_role TEXT NOT NULL,
            question TEXT NOT NULL,
            question_redacted TEXT NOT NULL,
            risk_reason TEXT NOT NULL,
            status TEXT NOT NULL,
            reviewer_role TEXT,
            decision_ts_unix REAL,
            decision TEXT
        )
        """
    )
    conn.commit()
    conn.close()


@dataclass(frozen=True)
class SourceRef:
    source: str
    page: int | None
    chunk_id: str | None
    score: float | None


def write_ingest_event(*, event_id: str, actor_role: str, folder_path: str, file_count: int, chunk_count: int) -> None:
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO ingest_events (id, ts_unix, actor_role, folder_path, file_count, chunk_count)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (event_id, time.time(), actor_role, folder_path, file_count, chunk_count),
    )
    conn.commit()
    conn.close()


def write_query_event(
    *,
    event_id: str,
    actor_role: str,
    question: str,
    question_redacted: str,
    risk_level: str,
    escalation_ticket_id: str | None,
    retrieved_k: int,
    sources: Iterable[SourceRef],
    answer: str | None,
    answer_redacted: str | None,
) -> None:
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO query_events
          (id, ts_unix, actor_role, question, question_redacted, risk_level, escalation_ticket_id, retrieved_k, sources_json, answer, answer_redacted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            time.time(),
            actor_role,
            question,
            question_redacted,
            risk_level,
            escalation_ticket_id,
            retrieved_k,
            json.dumps([asdict(s) for s in sources]),
            answer,
            answer_redacted,
        ),
    )
    conn.commit()
    conn.close()


def create_escalation_ticket(
    *,
    ticket_id: str,
    actor_role: str,
    question: str,
    question_redacted: str,
    risk_reason: str,
) -> None:
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO escalation_tickets
          (id, ts_unix, actor_role, question, question_redacted, risk_reason, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (ticket_id, time.time(), actor_role, question, question_redacted, risk_reason, "pending"),
    )
    conn.commit()
    conn.close()


def decide_escalation_ticket(*, ticket_id: str, reviewer_role: str, decision: str) -> dict[str, Any] | None:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM escalation_tickets WHERE id = ?", (ticket_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None
    if row["status"] != "pending":
        conn.close()
        return dict(row)

    conn.execute(
        """
        UPDATE escalation_tickets
        SET status = ?, reviewer_role = ?, decision_ts_unix = ?, decision = ?
        WHERE id = ?
        """,
        ("decided", reviewer_role, time.time(), decision, ticket_id),
    )
    conn.commit()
    cur.execute("SELECT * FROM escalation_tickets WHERE id = ?", (ticket_id,))
    updated = cur.fetchone()
    conn.close()
    return dict(updated) if updated else None


def list_recent_queries(limit: int = 50) -> list[dict[str, Any]]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM query_events ORDER BY ts_unix DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

