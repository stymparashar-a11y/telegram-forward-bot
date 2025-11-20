import logging
import datetime
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# --- CONFIG ---
BOT_TOKEN = "8003720292:AAH9EN5D57inOquULQCSj5kI4Uc-6iFqvIw"

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
    "batch_4": {
        "name": "Arjuna NEET 2026",
        "db_channel": -1003251243138,
        "main_channel": "@arjuna_neet_2026_1_0",
    },
}

# Store updated batches by date
updated_batches = {}

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# --- Helper functions ---
def today_str():
    return datetime.date.today().isoformat()

def get_updated_today():
    return updated_batches.get(today_str(), [])

def mark_updated(batch_id):
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

# --- Batch Menu Helper ---
async def show_batches(update_or_message, context, header="📋 Choose your batch (✅ = updated today):"):
    updated_today = get_updated_today()

    keyboard = []
    for batch_id, data in BATCHES.items():
        name = data["name"]
        if batch_id in updated_today:
            name += " ✅"
        keyboard.append([InlineKeyboardButton(name, callback_data=batch_id)])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if hasattr(update_or_message, "message"):  # /start or /statistic
        await update_or_message.message.reply_text(header, reply_markup=reply_markup)
    else:  # after update
        await update_or_message.reply_text(header, reply_markup=reply_markup)

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_batches(update, context)

# --- Batch Handler ---
async def batch_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
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
    await query.edit_message_text(f"{BATCHES[batch_id]['name']} selected. Choose an action:", reply_markup=reply_markup)

# --- Update Handler (ask for IDs) ---
async def update_batch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    batch_id = query.data.replace("update_", "")
    context.user_data["batch_id"] = batch_id
    await query.edit_message_text("✍️ Send video ID range in format: `start-end`\nExample: `10-15`", parse_mode="Markdown")

# --- Receive Video ID Range ---
async def receive_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "batch_id" not in context.user_data:
        return

    batch_id = context.user_data["batch_id"]
    db_channel = BATCHES[batch_id]["db_channel"]
    main_channel = BATCHES[batch_id]["main_channel"]

    try:
        text = update.message.text.strip()
        start_id, end_id = map(int, text.split("-"))
    except:
        await update.message.reply_text("⚠️ Invalid format. Use: `start-end`\nExample: `10-15`", parse_mode="Markdown")
        return

    sent_count = 0
    for msg_id in range(start_id, end_id + 1):
        try:
            await context.bot.copy_message(
                chat_id=main_channel,
                from_chat_id=db_channel,
                message_id=msg_id,
            )
            sent_count += 1
        except Exception as e:
            logging.warning(f"Message {msg_id} not found: {e}")

    # Mark this batch updated for today
    mark_updated(batch_id)

    # 🎉 Step 1: Fancy message
    template = random.choice(CONGRATS_STYLES)
    message = template.format(batch=BATCHES[batch_id]["name"], count=sent_count)
    await update.message.reply_text(message, parse_mode="Markdown")

    # 🎊 Step 2: Sticker
    sticker_id = random.choice(STICKERS)
    await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=sticker_id)

    # 🌸 Step 3: Emoji rain
    await update.message.reply_text("🎉🎊✨🌸🎆🎈🏆🍾✨🎊🎉")

    # Refresh menu with ticks
    await show_batches(update.message, context)

# --- Cancel Handler ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Cancelled.")
    await show_batches(query.message, context)

# --- Statistic Command ---
async def statistic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_batches(update, context, header=f"📊 Statistics for {today_str()} (✅ = updated today):")

# --- Main ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("statistic", statistic))
    app.add_handler(CallbackQueryHandler(batch_handler, pattern="^batch_"))
    app.add_handler(CallbackQueryHandler(update_batch, pattern="^update_"))
    app.add_handler(CallbackQueryHandler(cancel, pattern="^cancel$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_ids))

    app.run_polling()

if __name__ == "__main__":
    main()
