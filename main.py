#!/usr/bin/env python3
# parishram_batch_bot.py
# - Choose batch from inline menu
# - Send video ID range in format: start-end
# - Bot forwards in batches of 20 with 1-minute delay between batches
# - "Lock mode": while sending, all other actions are blocked

import logging
import datetime
import random
import asyncio  # for asyncio.sleep

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# --- CONFIG ---
BOT_TOKEN = "8003720292:AAH9EN5D57inOquULQCSj5kI4Uc-6iFqvIw"  # <-- keep this secret in real use

# Define mapping for each batch
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

# Store updated batches by date (in-memory)
updated_batches = {}

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --- Helper functions ---
def today_str() -> str:
    return datetime.date.today().isoformat()


def get_updated_today():
    return updated_batches.get(today_str(), [])


def mark_updated(batch_id: str):
    day = today_str()
    if day not in updated_batches:
        updated_batches[day] = []
    if batch_id not in updated_batches[day]:
        updated_batches[day].append(batch_id)


# --- Fancy Congrats ---
CONGRATS_STYLES = [
    "✨🎉 *Congratulations!* 🎉✨\n\n🔥 Batch *{batch}* updated successfully!\n📦 Total Videos Sent: *{count}*\n\n🏆 Keep it up!",
    "🎊💫 *Update Complete!* 💫🎊\n\n✅ Batch *{batch}* is shining green 🟢\n📦 Sent: *{count}* videos\n\n🚀 Onwards to success!",
    "🌟⚡ *Mission Accomplished!* ⚡🌟\n\n📂 Batch: *{batch}*\n📦 Videos Delivered: *{count}*\n\n🎆 Fireworks unlocked! 🎆",
    "🏅🎖 *Victory Unlocked!* 🎖🏅\n\n📂 Batch: *{batch}*\n📦 Count: *{count}*\n\n🌈 Fantastic job 💯",
    "🍾🥂 *Cheers!* 🥂🍾\n\nBatch *{batch}* successfully updated with *{count}* videos!\n\n🎈 Balloons up, celebrate 🎈",
]

# Example celebratory stickers (replace with your own file_ids if needed)
STICKERS = [
    "CAACAgUAAxkBAAIBQ2S9v9x3t3YcAAHcbShc7_wAAUmHoAAC6gIAAj-VyFYwU6oMnb4djTQE",  # Party
    "CAACAgUAAxkBAAIBRmS9v-KhM9P1D5zMBm-8AAHbG1vP0AAC-gIAAj-VyFZ7w9KrhH9H7TQE",  # Fireworks
    "CAACAgIAAxkBAAIBSWTA7tXwR99F2g8o8p9c8kfxFeW-AAI7AAOZPEwMH4TzISF3_kEzBA",     # Balloons
    "CAACAgIAAxkBAAIBSmTA7u2ZLSeIGwE4xOObcXhSoW3hAAK7AAPZPEwMXIkB5uWiEe0zBA",     # Trophy
    "CAACAgIAAxkBAAIBTGTBbbzX3mWnZz7tSuFLN85uP-M2AAJAAAPZPEwMiWnDPbrfZn8zBA",     # Champagne
]


# ---------------- LOCK MODE HELPERS ----------------
def is_sending(context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check global sending lock flag."""
    return context.application_data.get("is_sending", False)


def set_sending(context: ContextTypes.DEFAULT_TYPE, value: bool):
    """Set global sending lock flag."""
    context.application_data["is_sending"] = value


# --- Batch Menu Helper ---
async def show_batches(update_or_message, context: ContextTypes.DEFAULT_TYPE,
                       header="📋 Choose your batch (✅ = updated today):"):
    updated_today = get_updated_today()

    keyboard = []
    for batch_id, data in BATCHES.items():
        name = data["name"]
        if batch_id in updated_today:
            name += " ✅"
        keyboard.append([InlineKeyboardButton(name, callback_data=batch_id)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # update_or_message can be an Update or a Message
    if hasattr(update_or_message, "message"):  # e.g. /start or /statistic
        await update_or_message.message.reply_text(header, reply_markup=reply_markup)
    else:  # after update, when a Message is passed directly
        await update_or_message.reply_text(header, reply_markup=reply_markup)


# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_sending(context):
        await update.message.reply_text(
            "⏳ Videos are currently being forwarded in batches.\n\n"
            "Please wait until this upload is finished, then you can use the menu again."
        )
        return

    await show_batches(update, context)


# --- Statistic Command ---
async def statistic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_sending(context):
        await update.message.reply_text(
            "⏳ Videos are currently being forwarded in batches.\n\n"
            "Statistics will be available once the current upload is complete."
        )
        return

    await show_batches(
        update,
        context,
        header=f"📊 Statistics for {today_str()} (✅ = updated today):"
    )


# --- Batch Handler (from main menu) ---
async def batch_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if is_sending(context):
        await query.answer(
            "⏳ Videos are being forwarded right now.\nPlease wait until the upload finishes.",
            show_alert=True
        )
        return

    await query.answer()
    batch_id = query.data
    context.user_data["batch_id"] = batch_id

    keyboard = [
        [
            InlineKeyboardButton("✅ Update", callback_data=f"update_{batch_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"{BATCHES[batch_id]['name']} selected.\n\nChoose an action:",
        reply_markup=reply_markup,
    )


# --- Update Handler (ask for IDs) ---
async def update_batch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if is_sending(context):
        await query.answer(
            "⏳ Upload in progress.\nWait for it to finish before starting a new update.",
            show_alert=True
        )
        return

    await query.answer()
    batch_id = query.data.replace("update_", "")
    context.user_data["batch_id"] = batch_id

    await query.edit_message_text(
        "✍️ Send video ID range in format: `start-end`\n"
        "Example: `10-15`",
        parse_mode="Markdown",
    )


# --- Cancel Handler ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if is_sending(context):
        await query.answer(
            "⏳ Cannot cancel while upload is in progress.",
            show_alert=True
        )
        return

    await query.answer()
    await query.edit_message_text("❌ Cancelled.")
    await show_batches(query.message, context)


# --- Receive Video ID Range ---
async def receive_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # If no batch selected, ignore or give gentle hint
    if "batch_id" not in context.user_data:
        if is_sending(context):
            await update.message.reply_text(
                "⏳ Upload in progress. Please wait until it finishes."
            )
        # else: ignore random text
        return

    # If already sending, block new requests (LOCK MODE)
    if is_sending(context):
        await update.message.reply_text(
            "⏳ I am already forwarding a video batch.\n"
            "Please wait for the current upload to finish before sending a new range."
        )
        return

    batch_id = context.user_data["batch_id"]
    db_channel = BATCHES[batch_id]["db_channel"]
    main_channel = BATCHES[batch_id]["main_channel"]

    # Parse the range
    try:
        text = update.message.text.strip()
        start_id, end_id = map(int, text.split("-"))
        if start_id > end_id:
            raise ValueError("start > end")
    except Exception:
        await update.message.reply_text(
            "⚠️ Invalid format.\n\nUse: `start-end`\nExample: `10-15`",
            parse_mode="Markdown",
        )
        return

    # Set global sending lock
    set_sending(context, True)

    msg_ids = list(range(start_id, end_id + 1))
    total = len(msg_ids)
    sent_count = 0

    BATCH_SIZE = 20  # 20 videos per batch
    batch_number = 0

    await update.message.reply_text(
        f"🚀 Starting upload for *{BATCHES[batch_id]['name']}*.\n"
        f"Total videos to send: *{total}*.\n\n"
        f"Mode: 20 videos per batch with 1-minute gap.",
        parse_mode="Markdown",
    )

    try:
        for i in range(0, total, BATCH_SIZE):
            batch_number += 1
            chunk = msg_ids[i:i + BATCH_SIZE]

            await update.message.reply_text(
                f"📦 Sending batch *{batch_number}* "
                f"({len(chunk)} videos: IDs {chunk[0]}–{chunk[-1]})...",
                parse_mode="Markdown",
            )

            for msg_id in chunk:
                try:
                    await context.bot.copy_message(
                        chat_id=main_channel,
                        from_chat_id=db_channel,
                        message_id=msg_id,
                    )
                    sent_count += 1
                except Exception as e:
                    logger.warning(f"Message {msg_id} not found or failed: {e}")

            # If there are more batches left, wait 60 seconds
            if i + BATCH_SIZE < total:
                await update.message.reply_text(
                    "⏳ Batch sent.\nWaiting *60 seconds* before the next batch...",
                    parse_mode="Markdown",
                )
                await asyncio.sleep(60)

        # Mark this batch updated for today
        mark_updated(batch_id)

        # 🎉 Fancy message
        template = random.choice(CONGRATS_STYLES)
        message = template.format(batch=BATCHES[batch_id]["name"], count=sent_count)
        await update.message.reply_text(message, parse_mode="Markdown")

        # 🎊 Sticker
        sticker_id = random.choice(STICKERS)
        try:
            await context.bot.send_sticker(
                chat_id=update.effective_chat.id,
                sticker=sticker_id,
            )
        except Exception as e:
            logger.warning(f"Failed to send sticker: {e}")

        # 🌸 Emoji rain
        await update.message.reply_text("🎉🎊✨🌸🎆🎈🏆🍾✨🎊🎉")

        # Refresh menu with ticks
        await show_batches(update.message, context)

    finally:
        # Release global sending lock even if something fails
        set_sending(context, False)


# --- Main ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("statistic", statistic))

    # Callback queries (inline buttons)
    app.add_handler(CallbackQueryHandler(batch_handler, pattern="^batch_"))
    app.add_handler(CallbackQueryHandler(update_batch, pattern="^update_"))
    app.add_handler(CallbackQueryHandler(cancel, pattern="^cancel$"))

    # Text messages (ID range)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_ids))

    app.run_polling()


if __name__ == "__main__":
    main()
