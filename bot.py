# bot.py
import os
import asyncio
import requests
from threading import Thread
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN_ID = os.getenv("TOKEN_ID")
SN = os.getenv("SN")
BOT_TOKEN = os.getenv("BOT_TOKEN")

API_RT = "https://www.eu.solaxcloud.com/proxyApp/proxy/api/getRealtimeInfo.do"

app = Flask(__name__)

# создаём приложение telegram (Application из p-t-b v21+)
application = Application.builder().token(BOT_TOKEN).build()

# --- handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ok /status")

# не блокируем event loop — выполняем сетевой запрос в отдельном потоке
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # запускаем blocking requests.get в thread pool
        def do_request():
            return requests.get(API_RT, params={"tokenId": TOKEN_ID, "sn": SN}, timeout=15)
        resp = await asyncio.to_thread(do_request)
        try:
            data = resp.json()
        except Exception:
            data = {"error": "invalid json", "text": resp.text}
        # аккуратно форматируем (если JSON большой, можно сокращать)
        await update.message.reply_text(str(data))
    except Exception as e:
        # логируем ошибку и сообщаем пользователю
        await update.message.reply_text(f"Ошибка при запросе: {e}")
        raise

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("status", status))

# --- webhook route ---
@app.post(f"/webhook/{BOT_TOKEN}")
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    # Отправляем апдейт в очередь — приложение должно быть запущено (start)
    application.update_queue.put_nowait(update)
    return "ok"

# --- helper: run application.start() in background thread ---
def start_application_background():
    """
    This runs the telegram Application.start() coroutine in its own asyncio loop
    inside a background thread — so the dispatcher/worker runs and processes update_queue.
    """
    async def _run():
        # initialize and start the application (starts dispatcher & workers)
        await application.initialize()
        await application.start()
        # NOTE: we DO NOT call application.updater.start_polling() — webhook mode uses queue.
        # Keep coroutine running until cancelled (start() will keep workers alive).
        # We await on a never-ending event to keep this coroutine alive.
        await asyncio.Event().wait()

    asyncio.run(_run())

if __name__ == "__main__":
    # стартуем application в фоне
    t = Thread(target=start_application_background, daemon=True)
    t.start()

    # запускаем Flask как основный процесс (Render будет проксировать POST от Telegram)
    # Render автоматически назначает PORT env var.
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)

