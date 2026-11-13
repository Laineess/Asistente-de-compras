from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiosqlite

from app.bot.conversation import Session

SCHEMA = """
CREATE TABLE IF NOT EXISTS bot_sessions (
    user_id INTEGER PRIMARY KEY,
    chat_id INTEGER NOT NULL,
    estado TEXT NOT NULL,
    slots TEXT NOT NULL,
    modo TEXT NOT NULL,
    voz TEXT NOT NULL,
    actualizado_en TEXT NOT NULL
);
"""


class SessionStore:
    def __init__(self, db_path: Path | str, ttl_hours: int = 24) -> None:
        self.db_path = Path(db_path)
        self.ttl_hours = max(1, ttl_hours)

    async def init(self) -> None:
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(SCHEMA)
            await db.commit()

    async def save(self, session: Session) -> None:
        row = session.to_row()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO bot_sessions
                    (user_id, chat_id, estado, slots, modo, voz, actualizado_en)
                VALUES
                    (:user_id, :chat_id, :estado, :slots, :modo, :voz, :actualizado_en)
                ON CONFLICT(user_id) DO UPDATE SET
                    chat_id = excluded.chat_id,
                    estado = excluded.estado,
                    slots = excluded.slots,
                    modo = excluded.modo,
                    voz = excluded.voz,
                    actualizado_en = excluded.actualizado_en
                """,
                row,
            )
            await db.commit()

    async def get(self, user_id: int) -> Session | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM bot_sessions WHERE user_id = ?",
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()
        if row is None:
            return None
        session = Session.from_row(row)
        if self._expired(session):
            await self.delete(user_id)
            return None
        return session

    async def delete(self, user_id: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM bot_sessions WHERE user_id = ?", (user_id,))
            await db.commit()

    async def purge_expired(self) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.ttl_hours)
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM bot_sessions WHERE actualizado_en < ?",
                (cutoff.isoformat(),),
            )
            await db.commit()
            return cursor.rowcount if cursor.rowcount is not None else 0

    def _expired(self, session: Session) -> bool:
        updated = session.actualizado_en
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self.ttl_hours)
        return updated < cutoff
