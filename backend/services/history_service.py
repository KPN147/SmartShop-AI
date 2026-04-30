"""
SmartShop AI - Persistent Chat History Service
Lưu lịch sử hội thoại vào SQLite để không mất khi server restart.
Thay thế in-memory dict trong agent_service.py.
"""

import asyncio
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Đường dẫn file database SQLite
DB_PATH = Path(__file__).parent.parent / "data" / "chat_history.db"

# SQL để tạo bảng
_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS chat_sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT NOT NULL,
    role        TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content     TEXT NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_session_id ON chat_sessions(session_id);
"""


def _get_conn() -> sqlite3.Connection:
    """Tạo kết nối SQLite với row_factory để dễ đọc."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    """Khởi tạo database và tạo bảng nếu chưa có."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _get_conn() as conn:
        conn.executescript(_CREATE_TABLE_SQL)
    logger.info(f"[ChatHistoryDB] Database sẵn sàng tại: {DB_PATH}")


# Khởi tạo DB ngay khi import module
_init_db()


async def load_history(session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Tải lịch sử hội thoại gần nhất của một session.

    Args:
        session_id: ID phiên chat.
        limit: Số lượng tin nhắn gần nhất cần lấy (tính theo cặp hỏi/đáp).

    Returns:
        Danh sách dict [{"role": "user"|"assistant", "content": "..."}]
    """
    def _query():
        with _get_conn() as conn:
            rows = conn.execute(
                """
                SELECT role, content FROM (
                    SELECT role, content, created_at
                    FROM chat_sessions
                    WHERE session_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ) ORDER BY created_at ASC
                """,
                (session_id, limit * 2),  # limit * 2 vì mỗi cặp = 2 rows
            ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in rows]

    return await asyncio.get_event_loop().run_in_executor(None, _query)


async def save_message(session_id: str, role: str, content: str) -> None:
    """
    Lưu một tin nhắn vào database.

    Args:
        session_id: ID phiên chat.
        role: "user" hoặc "assistant".
        content: Nội dung tin nhắn.
    """
    def _insert():
        with _get_conn() as conn:
            conn.execute(
                "INSERT INTO chat_sessions (session_id, role, content) VALUES (?, ?, ?)",
                (session_id, role, content),
            )
            conn.commit()

    await asyncio.get_event_loop().run_in_executor(None, _insert)
    logger.debug(f"[ChatHistoryDB] Saved | session={session_id} | role={role}")


async def get_session_stats(session_id: str) -> Dict[str, Any]:
    """Lấy thống kê của một phiên chat (dùng cho debug/analytics)."""
    def _query():
        with _get_conn() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) as total_messages,
                    SUM(CASE WHEN role='user' THEN 1 ELSE 0 END) as user_messages,
                    SUM(CASE WHEN role='assistant' THEN 1 ELSE 0 END) as assistant_messages,
                    MIN(created_at) as first_message,
                    MAX(created_at) as last_message
                FROM chat_sessions WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
        return dict(row) if row else {}

    return await asyncio.get_event_loop().run_in_executor(None, _query)


async def delete_session(session_id: str) -> int:
    """Xóa toàn bộ lịch sử của một phiên chat. Trả về số rows đã xóa."""
    def _delete():
        with _get_conn() as conn:
            cur = conn.execute(
                "DELETE FROM chat_sessions WHERE session_id = ?", (session_id,)
            )
            conn.commit()
            return cur.rowcount

    deleted = await asyncio.get_event_loop().run_in_executor(None, _delete)
    logger.info(f"[ChatHistoryDB] Deleted {deleted} messages for session={session_id}")
    return deleted
