# 🏆 Telegram Auction Bot

Бот-аукцион для Telegram с перебивом ставок в **звёздах Telegram (XTR)**.  
Написан на **Python 3.10+** с использованием **aiogram 3.x** и **SQLite**.

---

## 📋 Возможности

- 🎯 Запуск аукциона командой `/start_auction` (только админ).
- ⭐ Приём ставок в звёздах Telegram (XTR) через инвойсы.
- 🔥 Автоматический перебив ставок с обновлением лидера.
- ⏱ Сброс таймера (5 минут) при каждой новой ставке.
- 🏁 Завершение аукциона по истечении времени без ставок.
- 🏆 Объявление победителя и уведомление заказчика в личку.
- 🔁 Автоматический перезапуск, если никто не поставил.
- 🚫 Без возврата ставок.
- 💵 Приз (доллары) выдаёт заказчик вручную.

---

## 📁 Структура проекта
auction_bot/
├── config.py # токен, ID админа и заказчика, параметры
├── database.py # работа с SQLite (aiosqlite)
├── auction.py # логика аукциона и таймеры
├── payments.py # инвойсы и обработка платежей XTR
├── handlers.py # команды и обработчики сообщений
├── main.py # точка входа
├── requirements.txt # зависимости
└── README.md

---

## ⚙️ Требования

- Python **3.10+**
- Telegram-бот, созданный в [@BotFather](https://t.me/BotFather)
- Включённые **Payments** в BotFather
- ID заказчика

---

## 🚀 Установка

### 1. Клонирование

```bash
git clone https://github.com/your-username/auction_bot.git
cd auction_bot
```
### 2. виртуальное окружение
```
python -m venv venv
source venv/bin/activate      # Linux / macOS
venv\Scripts\activate         # Windows
```
### 3. установка зависимостей
```
pip install -r requirements.txt
```
