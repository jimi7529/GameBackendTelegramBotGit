import os
import requests
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from fastapi import HTTPException

API_URL = os.getenv("API_URL", "http://localhost:8000")

# /health
async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = requests.get(f"{API_URL}/game/health")
        data = res.json()
        await update.message.reply_text(f"✅ API Status: {data['status']}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ API Error: {e}")

# /add_rps
async def add_rps_game_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = requests.post(f"{API_URL}/game/add-rps-game-type")
        await update.message.reply_text(res.json().get("message", "Unknown response"))
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# /create_room
async def create_game_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    payload = {
        "game_type": "rps",
        "telegram_id": user.id  # Ensure you're using the correct user ID (could be telegram_id or custom user_id)
    }
    
    print(user.id)

    try:
        res = requests.post(f"{API_URL}/game/create-room", json=payload)
        if res.status_code == 200:
            room_code = res.json().get("room_code")
            await update.message.reply_text(f"✅ Room created! Room code: {room_code}")
        else:
            await update.message.reply_text("❌ Error creating room.")
    except Exception as e:
        await update.message.reply_text("⚠️ Server error.")
        print("Error:", e)
        
# /play <ROOM_CODE> <MOVE>
async def play_rps_move(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) != 2:
            await update.message.reply_text("Usage: /play <ROOM_CODE> <MOVE>")
            return

        room_code, move = context.args
        payload = {
            "room_code": room_code,
            "telegram_id": str(update.effective_user.id),
            "move": move.lower()
        }

        res = requests.post(f"{API_URL}/game/rps/move", json=payload)

        if res.status_code != 200:
            await update.message.reply_text(f"❌ Error: {res.json().get('detail', 'Unknown error')}")
        else:
            res_data = res.json()
            await update.message.reply_text(res_data.get("status", "✅ Move submitted"))

    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")


# /end_session <ROOM_CODE>
async def end_rps_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            await update.message.reply_text("Usage: /end_session <ROOM_CODE>")
            return

        room_code = context.args[0]
        res = requests.post(f"{API_URL}/game/end-rps-session", params={"room_code": room_code})
        data = res.json()
        if "message" in data:
            result = data.get("result", {})
            await update.message.reply_text(
                f"✅ {data['message']}\n"
                f"👤 Player 1: {data['player_1']} played {data['move_1']}\n"
                f"👤 Player 2: {data['player_2']} played {data['move_2']}\n"
                f"🏆 Result: {result.get('result', 'N/A')}"
            )
        else:
            await update.message.reply_text(f"❌ Error: {data.get('error', 'Unknown')}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")

# Register command handlers
game_handlers = [
    CommandHandler("health", health_check),
    CommandHandler("add_rps", add_rps_game_type),
    CommandHandler("create_room", create_game_room),
    CommandHandler("play", play_rps_move),
    CommandHandler("end_session", end_rps_session),
]