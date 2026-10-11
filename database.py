# database.py
import aiosqlite
from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS auctions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                message_id INTEGER,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finished_at TIMESTAMP,
                winner_id INTEGER,
                winner_username TEXT,
                winner_amount INTEGER,
                is_active INTEGER DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bids (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                auction_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT,
                amount INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (auction_id) REFERENCES auctions(id)
            )
        """)
        await db.commit()


async def create_auction(chat_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO auctions (chat_id, is_active) VALUES (?, 1)",
            (chat_id,),
        )
        await db.commit()
        return cur.lastrowid


async def get_active_auction(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM auctions WHERE chat_id = ? AND is_active = 1 "
            "ORDER BY id DESC LIMIT 1",
            (chat_id,),
        )
        return await cur.fetchone()


async def add_bid(auction_id: int, user_id: int, username: str | None, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO bids (auction_id, user_id, username, amount) "
            "VALUES (?, ?, ?, ?)",
            (auction_id, user_id, username, amount),
        )
        await db.commit()


async def get_top_bid(auction_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM bids WHERE auction_id = ? "
            "ORDER BY amount DESC, created_at ASC LIMIT 1",
            (auction_id,),
        )
        return await cur.fetchone()


async def finish_auction(auction_id: int, winner_id, winner_username, amount):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE auctions SET is_active = 0, finished_at = CURRENT_TIMESTAMP, "
            "winner_id = ?, winner_username = ?, winner_amount = ? WHERE id = ?",
            (winner_id, winner_username, amount, auction_id),
        )
        await db.commit()


async def set_auction_message(auction_id: int, message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE auctions SET message_id = ? WHERE id = ?",
            (message_id, auction_id),
        )
        await db.commit()
