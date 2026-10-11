# config.py
BOT_TOKEN = "ВСТАВЬ_ТОКЕН_ОТ_BOTFATHER"
CUSTOMER_ID = 1808396633 # Telegram ID заказчика (узнать у @userinfobot)

# ID администратора, которому разрешено запускать /start_auction
ADMIN_ID = CUSTOMER_ID  # можно сделать отдельно

# Параметры аукциона
COOLDOWN_SECONDS = 5 * 60   # 5 минут
MIN_BID_STARS = 1           # минимальный шаг ставки (в звёздах)

DB_PATH = "auction.db"
