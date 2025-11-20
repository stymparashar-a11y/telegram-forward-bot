#!/usr/bin/env python3
import logging
import datetime
import random
import asyncio

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# BOT TOKEN
BOT_TOKEN = "8003720292:AAH9EN5D57inOquULQCSj5kI4Uc-6iFqvIw"

# Batch configuration
BATCHES = {
    "batch_1": {
        "name": "Parishram 2025",
        "db_channel": -1003048644664,
        "main_channel": "@parishram_2025_1_0",
    },
    "batch_2": {
        "name": "Parishram 2026",
        "db_channel": -1003048644664,
        "main_channel": "@parishram_2026_1_0",
    },
    "batch_3": {
        "name": "Arjuna JEE 2026",
        "db_channel": -1002944051263,
        "main_channel": "@arjuna_jee_1_0_2026",
    },
    "batch_4": {
        "name": "Lakshya JEE 2026",
        "db_channel": -1003465671248,
        "main_channel": -1002921200840,
    },
    "batch_5": {
        "name": "Arjuna NEET 2026",
        "db_channel": -1003251243138,
        "main_channel": "@arjuna_neet_2026_1_0",
    },
}

updated_batches = {}

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

def today():
    return datetime.date.today().isoformat()

def mark_updated(batch_id):
    if today() not in updated_batches:
        updated_batches[today()] = []
    if batch_id not in updated_batches[today()]:
        updated_batches[today()].append(batch_id)

def is_sending(context):
    return context.application_data.get("sending", False)

def set_sending(context, value):
    context.application_data["sending"] = value

CONGRATS = [
    "🎉 Batch *{batch}* updated successfully with *{count}* videos!",
    "🚀 Update complete for *{batch}*! Total videos sent: *{count}*",
    "✨ *{batch}* updated! Sent: *{count}* videos 🔥",
]

STICKERS = [
    "CAACAgUAAxkBAAIBQ2S9v9x3t3YcAAHcbShc7_wAAUmHoAAC6gIAAj-VyFYwU6oMnb4djTQE",
    "CAACAgUAAxkBAAIBRmS9v-KhM9P1D5zMBm-8AAHbG1vP0AAC-gIAAj-VyFZ7w9KrhH9H7TQE",
]

async def show_batches(update, context):
    kb = []
    done_today = updated_batches.get(today(), [])

    for batch_id, data in BATCHES.items():
        name = data["name"]
        if batch_id in done_today:
            name += " ✅"
        kb.append([InlineKeyboardButton(name, callback_data=batch_id)])

    await update.message.reply_text(
        "📦 Choose your batch:",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_sending(context):
        await update.message.reply_text("⏳ Upload in progress, please wait.")
        return
    await show_batches(update, context)

async def statistic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_batches(update, context)

async def batch_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if is_sending(context):
        await query.answer("Upload running. Wait.", show_alert=True)
        return

    batch_id = query.data
    context.user_data["batch_id"] = batch_id

    kb = [
        [
            InlineKeyboardButton("Update", callback_data=f"update_{batch_id}"),
            InlineKeyboardButton("Cancel", callback_data="cancel")
        ]
    ]

    await query.edit_message_text(
        f"{BATCHES[batch_id]['name']} selected.\nSend range like `10-20`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if is_sending(context):
        await q.answer("Cannot cancel during upload.", show_alert=True)
        return

    await q.edit_message_text("❌ Cancelled.")

async def update_batch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if is_sending(context):
        await q.answer("Upload running. Wait.", show_alert=True)
        return

    batch_id = q.data.replace("update_", "")
    context.user_data["batch_id"] = batch_id

    await q.edit_message_text(
        "Send video ID range like:\n`10-30`",
        parse_mode="Markdown"
    )

async def receive_range(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "batch_id" not in context.user_data:
        return

    if is_sending(context):
        await update.message.reply_text("⏳ Upload running. Wait.")
        return

    try:
        text = update.message.text.strip()
        start_id, end_id = map(int, text.split("-"))
    except:
        await update.message.reply_text("❌ Wrong format.\nUse `10-30`")
        return

    batch_id = context.user_data["batch_id"]
    db = BATCHES[batch_id]["db_channel"]
    chan = BATCHES[batch_id]["main_channel"]

    set_sending(context, True)
    ids = list(range(start_id, end_id + 1))
    total = len(ids)

    await update.message.reply_text(
        f"🚀 Starting upload of *{total}* videos.\n20 each batch, 1-minute wait.",
        parse_mode="Markdown"
    )

    sent = 0
    BATCH_SIZE = 20
    batch_no = 0

    try:
        for i in range(0, total, BATCH_SIZE):
            batch_no += 1
            chunk = ids[i:i + BATCH_SIZE]

            await update.message.reply_text(
                f"📦 Sending batch {batch_no}: {chunk[0]}–{chunk[-1]}"
            )

            for mid in chunk:
                try:
                    await context.bot.copy_message(
                        chat_id=chan,
                        from_chat_id=db,
                        message_id=mid
                    )
                    sent += 1
                except Exception as e:
                    logging.warning(f"Failed: {mid} — {e}")

            if i + BATCH_SIZE < total:
                await update.message.reply_text("⏳ Waiting 60 seconds...")
                await asyncio.sleep(60)

        mark_updated(batch_id)

        msg = random.choice(CONGRATS).format(batch=BATCHES[batch_id]["name"], count=sent)
        await update.message.reply_text(msg, parse_mode="Markdown")

        await context.bot.send_sticker(update.effective_chat.id, random.choice(STICKERS))

    finally:
        set_sending(context, False)

# MAIN
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("statistic", statistic))
    app.add_handler(CallbackQueryHandler(batch_select, pattern="^batch_"))
    app.add_handler(CallbackQueryHandler(update_batch, pattern="^update_"))
    app.add_handler(CallbackQueryHandler(cancel, pattern="^cancel"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_range))

    app.run_polling()

if __name__ == "__main__":
    main()
