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
                file_type TEXT NOT NULL
            )
            """
        )
        await db.commit()


async def add_movie(code: str, title: str, file_id: str, file_type: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO movies (code, title, file_id, file_type) VALUES (?, ?, ?, ?)",
            (code, title, file_id, file_type),
        )
        await db.commit()


async def get_movie(code: str):
    """(title, file_id, file_type) yoki None qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT title, file_id, file_type FROM movies WHERE code = ?", (code,)
        ) as cur:
            return await cur.fetchone()


async def movie_exists(code: str) -> bool:
    return await get_movie(code) is not None


async def delete_movie(code: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM movies WHERE code = ?", (code,))
        await db.commit()


async def count_movies() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM movies") as cur:
            row = await cur.fetchone()
            return row[0]


async def get_movies_page(page: int, page_size: int):
    """[(code, title), ...] qaytaradi."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT code, title FROM movies ORDER BY rowid LIMIT ? OFFSET ?",
            (page_size, page * page_size),
        ) as cur:
            return await cur.fetchall()
