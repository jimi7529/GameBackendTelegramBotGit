from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    payload = {
        "telegram_id": str(user.id),
        "username": user.username or "unknown"
    }

    try:
        res = requests.post(f"{API_URL}/api/users/sync", json=payload)
        if res.status_code == 200:
            await update.message.reply_text("✅ Registered successfully!")
        else:
            await update.message.reply_text("❌ Error registering.")
    except Exception as e:
        await update.message.reply_text("⚠️ Server error.")
        print("Error:", e)

start_handler = CommandHandler("start", start)
