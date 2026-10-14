"""SQLite storage for SugarBalance SA health logs."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "sugarbalance.db"


def get_connection() -> sqlite3.Connection:
    """Create a local SQLite connection with row access by column name."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database() -> None:
    """Create application tables if they do not exist."""
    connection = get_connection()
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS health_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recorded_at TEXT NOT NULL,
                systolic INTEGER,
                diastolic INTEGER,
                glucose REAL,
                notes TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id INTEGER NOT NULL,
                operation TEXT NOT NULL,
                created_at TEXT NOT NULL,
                synced INTEGER NOT NULL DEFAULT 0 CHECK (synced IN (0, 1))
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def add_health_log(
    systolic: Optional[int] = None,
    diastolic: Optional[int] = None,
    glucose: Optional[float] = None,
    notes: str = "",
) -> int:
    """Insert a health measurement and return its row id."""
    connection = get_connection()
    try:
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
        cursor = connection.execute(
            """
            INSERT INTO health_logs
                (recorded_at, systolic, diastolic, glucose, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (timestamp, systolic, diastolic, glucose, notes),
        )
        connection.execute(
            """
            INSERT INTO sync_queue (entity_type, entity_id, operation, created_at)
            VALUES (?, ?, ?, ?)
            """,
            ("health_log", cursor.lastrowid, "upsert", timestamp),
        )
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def get_recent_logs(limit: int = 20) -> List[Dict]:
    """Return the most recent health readings."""
    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            SELECT id, recorded_at, systolic, diastolic, glucose, notes
            FROM health_logs
            ORDER BY recorded_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


def get_health_log(log_id: int) -> Optional[Dict]:
    """Return a single health log, or None if it does not exist."""
    connection = get_connection()
    try:
        cursor = connection.execute(
            "SELECT * FROM health_logs WHERE id = ?",
            (log_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        connection.close()


def delete_health_log(log_id: int) -> None:
    """Delete a health log and queue its deletion for future synchronization."""
    connection = get_connection()
    try:
        cursor = connection.execute(
            "DELETE FROM health_logs WHERE id = ?",
            (log_id,),
        )
        if cursor.rowcount:
            timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
            connection.execute(
                """
                INSERT INTO sync_queue (entity_type, entity_id, operation, created_at)
                VALUES (?, ?, ?, ?)
                """,
                ("health_log", log_id, "delete", timestamp),
            )
        connection.commit()
    finally:
        connection.close()


def get_pending_sync_items(limit: int = 100) -> List[Dict]:
    """Return unsynced local changes in queue order."""
    if limit < 1:
        raise ValueError("Limit must be greater than zero.")
    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            SELECT id, entity_type, entity_id, operation, created_at, synced
            FROM sync_queue
            WHERE synced = 0
            ORDER BY id
            LIMIT ?
            """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


def mark_sync_item_synced(queue_id: int) -> bool:
    """Mark a queue item as synced after a future sync worker confirms it."""
    connection = get_connection()
    try:
        cursor = connection.execute(
            "UPDATE sync_queue SET synced = 1 WHERE id = ? AND synced = 0",
            (queue_id,),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def clear_all_logs() -> None:
    """Delete all health logs and queue each deletion for future synchronization."""
    connection = get_connection()
    try:
        log_ids = [
            row["id"]
            for row in connection.execute("SELECT id FROM health_logs").fetchall()
        ]
        connection.execute("DELETE FROM health_logs")
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
        connection.executemany(
            """
            INSERT INTO sync_queue (entity_type, entity_id, operation, created_at)
            VALUES (?, ?, ?, ?)
            """,
            [
                ("health_log", log_id, "delete", timestamp)
                for log_id in log_ids
            ],
        )
        connection.commit()
    finally:
        connection.close()
