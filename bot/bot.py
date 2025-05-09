from telegram.ext import ApplicationBuilder
from handlers.start import start_handler
from handlers.game import game_handlers

import os
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(start_handler)
app.add_handlers(game_handlers)

if __name__ == "__main__":
    app.run_polling()
