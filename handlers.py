# handlers.py
import re

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, PreCheckoutQuery, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import auction
import payments
from config import ADMIN_ID

router = Router()


# ---------- /start_auction ----------
@router.message(Command("start_auction"))
async def cmd_start_auction(message: Message, bot: Bot):
    if message.from_user.id != ADMIN_ID:
        await message.reply("⛔ Только админ может запускать аукцион.")
        return
    await auction.start_auction(bot, message.chat.id)


# ---------- /bid <amount> ----------
@router.message(Command("bid"))
async def cmd_bid(message: Message, bot: Bot):
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].isdigit():
        await message.reply("Использование: <code>/bid 10</code>", parse_mode="HTML")
        return

    amount = int(args[1])
    state = auction.get_state(message.chat.id)
    if not state:
        await message.reply("Сейчас нет активного аукциона.")
        return

    # Проверяем «перебив» до отправки инвойса — чтобы не гонять оплату зря
    from database import get_top_bid
    top = await get_top_bid(state.auction_id)
    current = top["amount"] if top else 0
    if amount <= current:
        await message.reply(f"❌ Ставка должна быть выше текущей ({current} ⭐).")
        return

    # Отправляем инвойс в личку пользователю
    try:
        await payments.send_bid_invoice(
            bot, user_id=message.from_user.id,
            amount=amount, auction_id=state.auction_id,
        )
        await message.reply("📩 Инвойс отправлен вам в личку. Оплатите для подтверждения ставки.")
    except Exception as e:
        await message.reply(f"⚠️ Не удалось отправить инвойс: {e}\n"
                            f"Убедитесь, что вы начали диалог с ботом.")


# ---------- /bid от пользователя в ЛС (альтернатива) ----------
@router.message(F.chat.type == "private", Command("bid"))
async def cmd_bid_private(message: Message, bot: Bot):
    await message.reply(
        "Ставки делаются в чате аукциона командой <code>/bid &lt;сумма&gt;</code>.",
        parse_mode="HTML",
    )


# ---------- Pre-checkout ----------
@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await payments.answer_pre_checkout(query)


# ---------- Successful payment ----------
@router.message(F.successful_payment)
async def on_successful_payment(message: Message, bot: Bot):
    auction_id, amount = await payments.handle_successful_payment(message)

    # Находим чат по auction_id
    from database import DB_PATH
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT chat_id FROM auctions WHERE id = ?", (auction_id,)
        )
        row = await cur.fetchone()

    if not row:
        await message.answer("⚠️ Аукцион не найден.")
        return

    chat_id = row["chat_id"]
    ok, text = await auction.register_bid(
        bot,
        chat_id=chat_id,
        user_id=message.from_user.id,
        username=message.from_user.username,
        amount=amount,
    )

    await message.answer("✅ Оплата получена. Ваша ставка зарегистрирована.")
    if ok:
        await bot.send_message(chat_id, text, parse_mode="HTML")


# ---------- /help ----------
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.reply(
        "📖 <b>Команды</b>\n"
        "/start_auction — запустить аукцион (только админ)\n"
        "/bid &lt;сумма&gt; — сделать ставку в звёздах\n"
        "/help — эта справка",
        parse_mode="HTML",
    )
