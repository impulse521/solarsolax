import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import requests
from flask import Flask, request

TOKEN_ID = os.getenv("20251101220631165040670")      # положишь в env
SN = os.getenv("SRJEZGKTMG")                  # положишь в env
BOT_TOKEN = os.getenv("8330351071:AAFmcE9Ol783Aay0FMcHC6yZW5OfilSMP7o")    # положишь в env

API_RT = "https://www.solaxcloud.com/proxy/api/v5/inverter/getRealtimeInfo"

app = Flask(__name__)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    r = requests.get(API_RT, params={"tokenId": TOKEN_ID, "sn": SN})
    await update.message.reply_text(str(r.json()))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ok /status")

@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

if __name__ == "__main__":
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))

    # запускаем веб сервер flask (для render)
    from threading import Thread
    Thread(target=application.run_polling, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

