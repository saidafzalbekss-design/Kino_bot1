import time

import asyncpg

from config import DATABASE_URL

_pool: asyncpg.Pool | None = None


async def init_db() -> None:
    """Postgres'ga ulanadi va jadvallarni yaratadi (bor bo'lsa tegmaydi)."""
    global _pool
    if not DATABASE_URL:
        raise SystemExit(
            "DATABASE_URL topilmadi. Render'da Environment Variables ga qo'shing."
        )
    _pool = await asyncpg.create_pool(
        DATABASE_URL, min_size=1, max_size=5, statement_cache_size=0, command_timeout=30
    )
    async with _pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS movies (
                id        BIGSERIAL PRIMARY KEY,
                code      TEXT UNIQUE NOT NULL,
                title     TEXT NOT NULL,
                file_id   TEXT NOT NULL,
                file_type TEXT NOT NULL,
                is_vip    BOOLEAN NOT NULL DEFAULT FALSE
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS vip_users (
                user_id    BIGINT PRIMARY KEY,
                expires_at BIGINT
            )
            """
        )


def _affected(status: str) -> int:
    return int(status.split()[-1])


# ============ Kinolar ============
async def add_movie(
    code: str, title: str, file_id: str, file_type: str, is_vip: bool = False
) -> None:
    async with _pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO movies (code, title, file_id, file_type, is_vip) "
            "VALUES ($1, $2, $3, $4, $5)",
            code, title, file_id, file_type, bool(is_vip),
        )


async def get_movie(code: str):
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT title, file_id, file_type, is_vip FROM movies WHERE code = $1",
            code,
        )
    return (row["title"], row["file_id"], row["file_type"], row["is_vip"]) if row else None


async def movie_exists(code: str) -> bool:
    return await get_movie(code) is not None


async def delete_movie(code: str) -> None:
    async with _pool.acquire() as conn:
        await conn.execute("DELETE FROM movies WHERE code = $1", code)


async def set_movie_vip(code: str, is_vip: bool) -> bool:
    async with _pool.acquire() as conn:
        status = await conn.execute(
            "UPDATE movies SET is_vip = $1 WHERE code = $2", bool(is_vip), code
        )
    return _affected(status) > 0


def _vip_where(vip: bool | None) -> str:
    if vip is None:
        return ""
    return "WHERE is_vip = TRUE" if vip else "WHERE is_vip = FALSE"


async def count_movies(vip: bool | None = None) -> int:
    async with _pool.acquire() as conn:
        return await conn.fetchval(f"SELECT COUNT(*) FROM movies {_vip_where(vip)}")


async def get_movies_page(page: int, page_size: int, vip: bool | None = None):
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT code, title, is_vip FROM movies {_vip_where(vip)} "
            "ORDER BY id LIMIT $1 OFFSET $2",
            page_size, page * page_size,
        )
    return [(r["code"], r["title"], r["is_vip"]) for r in rows]


# ============ VIP foydalanuvchilar ============
async def add_vip(user_id: int, days: int | None = None) -> None:
    expires = None if days is None else int(time.time()) + days * 86400
    async with _pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO vip_users (user_id, expires_at) VALUES ($1, $2) "
            "ON CONFLICT (user_id) DO UPDATE SET expires_at = EXCLUDED.expires_at",
            user_id, expires,
        )


async def remove_vip(user_id: int) -> bool:
    async with _pool.acquire() as conn:
        status = await conn.execute("DELETE FROM vip_users WHERE user_id = $1", user_id)
    return _affected(status) > 0


async def is_vip(user_id: int) -> bool:
    async with _pool.acquire() as conn:
        expires = await conn.fetchrow(
            "SELECT expires_at FROM vip_users WHERE user_id = $1", user_id
        )
    if not expires:
        return False
    return expires["expires_at"] is None or expires["expires_at"] > time.time()


async def list_vips():
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT user_id, expires_at FROM vip_users "
            "WHERE expires_at IS NULL OR expires_at > $1 ORDER BY user_id",
            int(time.time()),
        )
    return [(r["user_id"], r["expires_at"]) for r in rows]
