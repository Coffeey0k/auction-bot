# auction.py
import asyncio
import time
from typing import Optional

from aiogram import Bot

from config import COOLDOWN_SECONDS, CUSTOMER_ID
from database import (
    create_auction,
    get_active_auction,
    get_top_bid,
    finish_auction,
    set_auction_message,
)


class AuctionState:
    """Хранит состояние текущего аукциона в памяти."""
    def __init__(self, auction_id: int, chat_id: int):
        self.auction_id = auction_id
        self.chat_id = chat_id
        self.end_time: float = time.time() + COOLDOWN_SECONDS
        self.task: Optional[asyncio.Task] = None
        self.lock = asyncio.Lock()


# Словарь: chat_id -> AuctionState
_active_auctions: dict[int, AuctionState] = {}


def get_state(chat_id: int) -> Optional[AuctionState]:
    return _active_auctions.get(chat_id)


async def start_auction(bot: Bot, chat_id: int):
    """Запускает новый аукцион."""
    if chat_id in _active_auctions:
        await bot.send_message(chat_id, "⚠️ Аукцион уже идёт в этом чате.")
        return

    auction_id = await create_auction(chat_id)
    state = AuctionState(auction_id, chat_id)
    _active_auctions[chat_id] = state

    msg = await bot.send_message(
        chat_id,
        "🎉 <b>Аукцион начат!</b>\n"
        "Ставка: <b>0 звёзд</b>.\n"
        "Кулдаун: <b>5 минут</b>.",
        parse_mode="HTML",
    )
    await set_auction_message(auction_id, msg.message_id)

    state.task = asyncio.create_task(_timer_loop(bot, chat_id))


async def register_bid(bot: Bot, chat_id: int, user_id: int,
                       username: Optional[str], amount: int) -> tuple[bool, str]:
    """
    Регистрирует ставку. Возвращает (успех, текст_ответа).
    """
    state = get_state(chat_id)
    if not state:
        return False, "Сейчас нет активного аукциона."

    top = await get_top_bid(state.auction_id)
    current = top["amount"] if top else 0

    if amount <= current:
        return False, f"❌ Ставка должна быть выше текущей ({current} ⭐)."

    # Обновляем ставку
    prev_leader_id = top["user_id"] if top else None
    from database import add_bid
    await add_bid(state.auction_id, user_id, username, amount)

    # Сброс таймера
    async with state.lock:
        state.end_time = time.time() + COOLDOWN_SECONDS

    name = f"@{username}" if username else f"id{user_id}"
    remaining = _fmt_remaining(state.end_time)

    if prev_leader_id is None:
        text = (
            f"✅ <b>Ставка принята!</b>\n"
            f"Лидер: {name}\n"
            f"Сумма: <b>{amount} ⭐</b>\n"
            f"До конца: <b>{remaining}</b>"
        )
    else:
        text = (
            f"🔥 <b>Ставка перебита!</b>\n"
            f"Новый лидер: {name}\n"
            f"Сумма: <b>{amount} ⭐</b>\n"
            f"До конца: <b>{remaining}</b>"
        )

    return True, text


async def _timer_loop(bot: Bot, chat_id: int):
    """Периодически проверяет, не истёк ли таймер. Раз в секунду."""
    try:
        while True:
            state = _active_auctions.get(chat_id)
            if not state:
                return

            now = time.time()
            async with state.lock:
                end_time = state.end_time

            if now >= end_time:
                await _finish(bot, chat_id)
                return

            await asyncio.sleep(1)
    except asyncio.CancelledError:
        return


async def _finish(bot: Bot, chat_id: int):
    state = _active_auctions.pop(chat_id, None)
    if not state:
        return

    top = await get_top_bid(state.auction_id)

    if not top:
        # Никто не поставил — перезапускаем
        await bot.send_message(
            chat_id,
            "⏳ Время вышло, но ставок не было.\n"
            "🔁 <b>Аукцион начинается заново!</b>",
            parse_mode="HTML",
        )
        await finish_auction(state.auction_id, None, None, None)
        await asyncio.sleep(1)
        await start_auction(bot, chat_id)
        return

    name = f"@{top['username']}" if top["username"] else f"id{top['user_id']}"
    await bot.send_message(
        chat_id,
        f"🏆 <b>Время вышло!</b>\n"
        f"Победитель: {name}\n"
        f"Ставка: <b>{top['amount']} ⭐</b>",
        parse_mode="HTML",
    )
    await finish_auction(
        state.auction_id, top["user_id"], top["username"], top["amount"]
    )

    # Уведомляем заказчика в личку
    try:
        await bot.send_message(
            CUSTOMER_ID,
            f"📢 <b>Аукцион завершён!</b>\n"
            f"Чат: <code>{chat_id}</code>\n"
            f"Победитель: {name} (id: <code>{top['user_id']}</code>)\n"
            f"Ставка: <b>{top['amount']} ⭐</b>\n\n",
            parse_mode="HTML",
        )
    except Exception as e:
        print(f"[warn] не удалось уведомить заказчика: {e}")


def _fmt_remaining(end_time: float) -> str:
    left = max(0, int(end_time - time.time()))
    m, s = divmod(left, 60)
    return f"{m}:{s:02d}"
