# payments.py
from aiogram import Bot
from aiogram.types import LabeledPrice, PreCheckoutQuery, Message

from config import MIN_BID_STARS


async def send_bid_invoice(bot: Bot, chat_id: int, amount: int, auction_id: int):
    """
    Отправляет инвойс на оплату amount звёзд.
    В payload кладём auction_id + сумму, чтобы потом проверить.
    """
    if amount < MIN_BID_STARS:
        raise ValueError(f"Минимальная ставка — {MIN_BID_STARS} ⭐")

    prices = [LabeledPrice(label=f"Ставка {amount} ⭐", amount=amount)]
    await bot.send_invoice(
        chat_id=chat_id,
        title="Ставка на аукционе",
        description=f"Ставка {amount} звёзд. Возврат невозможен.",
        payload=f"auction:{auction_id}:{amount}",
        provider_token="",       # для XTR пустой
        currency="XTR",
        prices=prices,
        start_parameter="bid",
    )


async def answer_pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)


async def handle_successful_payment(message: Message) -> tuple[int, int]:
    """
    Возвращает (auction_id, amount) из payload.
    """
    payload = message.successful_payment.invoice_payload
    parts = payload.split(":")
    auction_id = int(parts[1])
    amount = int(parts[2])
    return auction_id, amount
