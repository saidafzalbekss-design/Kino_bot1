import time

import aiosqlite

from config import DB_PATH


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS movies (
                code      TEXT PRIMARY KEY,
                title     TEXT NOT NULL,
                file_id   TEXT NOT NULL,
                file_type TEXT NOT NULL,
                is_vip    INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        # Eski bazada is_vip ustuni bo'lmasa, qo'shib qo'yamiz
        async with db.execute("PRAGMA table_info(movies)") as cur:
            cols = [row[1] for row in await cur.fetchall()]
        if "is_vip" not in cols:
            await db.execute(
                "ALTER TABLE movies ADD COLUMN is_vip INTEGER NOT NULL DEFAULT 0"
            )

        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS vip_users (
                user_id    INTEGER PRIMARY KEY,
                expires_at INTEGER          -- NULL = muddatsiz
            )
            """
        )
        await db.commit()


# ============ Kinolar ============
async def add_movie(
    code: str, title: str, file_id: str, file_type: str, is_vip: bool = False
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO movies (code, title, file_id, file_type, is_vip) "
            "VALUES (?, ?, ?, ?, ?)",
            (code, title, file_id, file_type, int(is_vip)),
        )
        await db.commit()


async def get_movie(code: str):
    """(title, file_id, file_type, is_vip) yoki None qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT title, file_id, file_type, is_vip FROM movies WHERE code = ?",
            (code,),
        ) as cur:
            row = await cur.fetchone()
            return (row[0], row[1], row[2], bool(row[3])) if row else None


async def movie_exists(code: str) -> bool:
    return await get_movie(code) is not None


async def delete_movie(code: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM movies WHERE code = ?", (code,))
        await db.commit()


async def set_movie_vip(code: str, is_vip: bool) -> bool:
    """Kinoni VIP qiladi / oddiy qiladi. Kino topilmasa False."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "UPDATE movies SET is_vip = ? WHERE code = ?", (int(is_vip), code)
        )
        await db.commit()
        return cur.rowcount > 0


def _vip_where(vip: bool | None) -> str:
    if vip is None:
        return ""
    return "WHERE is_vip = 1" if vip else "WHERE is_vip = 0"


async def count_movies(vip: bool | None = None) -> int:
    """vip=None -> hammasi, True -> faqat VIP, False -> faqat oddiy."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            f"SELECT COUNT(*) FROM movies {_vip_where(vip)}"
        ) as cur:
            row = await cur.fetchone()
            return row[0]


async def get_movies_page(page: int, page_size: int, vip: bool | None = None):
    """[(code, title, is_vip), ...] qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            f"SELECT code, title, is_vip FROM movies {_vip_where(vip)} "
            "ORDER BY rowid LIMIT ? OFFSET ?",
            (page_size, page * page_size),
        ) as cur:
            rows = await cur.fetchall()
            return [(code, title, bool(v)) for code, title, v in rows]


# ============ VIP foydalanuvchilar ============
async def add_vip(user_id: int, days: int | None = None) -> None:
    """days=None -> muddatsiz VIP. Aks holda hozirdan boshlab shuncha kun."""
    expires = None if days is None else int(time.time()) + days * 86400
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO vip_users (user_id, expires_at) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET expires_at = excluded.expires_at",
            (user_id, expires),
        )
        await db.commit()


async def remove_vip(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM vip_users WHERE user_id = ?", (user_id,))
        await db.commit()
        return cur.rowcount > 0


async def is_vip(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT expires_at FROM vip_users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
    if not row:
        return False
    return row[0] is None or row[0] > time.time()


async def list_vips():
    """[(user_id, expires_at yoki None), ...] — muddati o'tmaganlar."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, expires_at FROM vip_users "
            "WHERE expires_at IS NULL OR expires_at > ? ORDER BY rowid",
            (int(time.time()),),
        ) as cur:
            return await cur.fetchall()
