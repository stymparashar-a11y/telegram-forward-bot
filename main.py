import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import re
import os

BOT_TOKEN = os.getenv("BOT_TOKEN") or "YOUR_BOT_TOKEN"
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME") or "YOUR_CHANNEL_USERNAME"

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    match = re.search(r"v=(\d+)", query)
    if match:
        message_id = int(match.group(1))
        try:
            await context.bot.forward_message(chat_id=update.effective_chat.id,
                                              from_chat_id=CHANNEL_USERNAME,
                                              message_id=message_id)
        except Exception as e:
            await update.message.reply_text("Error forwarding message.")
            logging.error(e)
    else:
        await update.message.reply_text("Please provide a valid ID using ?v=ID format.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
