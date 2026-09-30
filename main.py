import os
import random
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")

VOLTX_API_KEY = "MHPU3S5IV1A"
YOUR_TELEGRAM_USERNAME = "smmsaport"

USER_STATES = {}
USER_RANGES = {}

LIVE_RANGES = [
    ("23762XXX", 37),
    ("237622XXX", 25),
    ("237620XXX", 13),
    ("225072XXX", 10),
    ("22896XXX", 7),
    ("2290163XXX", 6),
    ("26661XXX", 6),
    ("22897XXX", 4),
    ("25567XXX", 4),
    ("22890XXX", 3),
]

def get_country_info(phone_number):
    clean_num = phone_number.replace("+", "").strip()
    
    if clean_num.startswith("237"):
        return "🇨🇲 CAMEROON (CM)", "cm"
    elif clean_num.startswith("225"):
        return "🇨🇮 IVORY COAST (CI)", "ci"
    elif clean_num.startswith("228"):
        return "🇹🇬 TOGO (TG)", "tg"
    elif clean_num.startswith("229"):
        return "🇧🇯 BENIN (BJ)", "bj"
    elif clean_num.startswith("255"):
        return "🇹🇿 TANZANIA (TZ)", "tz"
    elif clean_num.startswith("266"):
        return "🇱🇸 LESOTHO (LS)", "ls"
    else:
        return "🇨🇮 IVORY COAST (CI)", "ci"

def generate_numbers_list(clean_prefix, count=3):
    numbers = []
    for _ in range(count):
        random_suffix = "".join([str(random.randint(0, 9)) for _ in range(5)])
        numbers.append(f"+{clean_prefix}{random_suffix}")
    return numbers

def create_multi_number_markup(numbers_list):
    keyboard = []
    for num in numbers_list:
        keyboard.append([InlineKeyboardButton(f"👤 📋 {num}", callback_data=f"num_{num}")])
    
    keyboard.append([InlineKeyboardButton("🔄 Change Number", callback_data="change_number")])
    keyboard.append([InlineKeyboardButton("🌐 Change Country", callback_data="change_country")])
    keyboard.append([InlineKeyboardButton("📣 OTP Group ↗", url=f"https://t.me/{YOUR_TELEGRAM_USERNAME}")])
    
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [
        ["📞 Get API Number", "⚙️ Set Range"],
        ["🟢 Live Traffic", "💳 Balance"],
        ["📣 OTP Group"]
    ]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    await update.message.reply_text("Welcome to FB MASTER NUMBER bot! 🤖\nPlease select an option from the menu below:", reply_markup=markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if USER_STATES.get(user_id) == "WAITING_FOR_RANGE":
        if "x" in text.lower() or text.isdigit():
            USER_STATES[user_id] = None
            USER_RANGES[user_id] = text
            await update.message.reply_text(f"🔴 Target range updated to: `{text}`", parse_mode="Markdown")
        else:
            await update.message.reply_text("🔴 Invalid range! Please enter a valid number prefix (e.g. 5198xxxxxx or 1234xxxx).")
        return

    if text == "📞 Get API Number":
        await update.message.reply_text("⏳ Requesting numbers...")
        
        user_range = USER_RANGES.get(user_id, "23762")
        clean_prefix = user_range.lower().replace("x", "")
        
        country_display, _ = get_country_info(clean_prefix)
        numbers = generate_numbers_list(clean_prefix, 3)
        
        num_text = "\n".join([f"📱 `{num}`" for num in numbers])
        
        header_text = f"❓ Service: 📘 Facebook\n{country_display}\n\n{num_text}\n\n⏳ Waiting for OTP..."
        reply_markup = create_multi_number_markup(numbers)
        await update.message.reply_text(header_text, reply_markup=reply_markup, parse_mode="Markdown")

    elif text == "⚙️ Set Range":
        USER_STATES[user_id] = "WAITING_FOR_RANGE"
        await update.message.reply_text("🔴 Please send your target number range (e.g. 5198xxxxxx or 1234xxxx):")

    elif text == "🟢 Live Traffic":
        traffic_lines = ["📊 **AVAILABLE RANGE TRAFFIC LIST**\n"]
        for r_code, count in LIVE_RANGES:
            country_display, _ = get_country_info(r_code)
            traffic_lines.append(f"🌐 `{r_code}` - FB - **{count}** | {country_display}")
        
        traffic_lines.append("\n⚡ Select a range and use **⚙️ Set Range** to target it!")
        await update.message.reply_text("\n".join(traffic_lines), parse_mode="Markdown")

    elif text == "💳 Balance":
        balance_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Withdraw via Binance", callback_data="withdraw_binance")],
            [InlineKeyboardButton("🔴 Set Binance ID", callback_data="set_binance")],
            [InlineKeyboardButton("📣 OTP Group ↗️", url=f"https://t.me/{YOUR_TELEGRAM_USERNAME}")]
        ])
        await update.message.reply_text("Current Balance: $0.091\nBinance Pay ID: Not Set\n\nMinimum withdraw is $0.2", reply_markup=balance_markup)

    elif text == "📣 OTP Group":
        await update.message.reply_text(f"📣 Join our OTP Group: t.me/{YOUR_TELEGRAM_USERNAME}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "change_number":
        user_id = query.from_user.id
        
        user_range = USER_RANGES.get(user_id, "23762")
        clean_prefix = user_range.lower().replace("x", "")
        
        country_display, _ = get_country_info(clean_prefix)
        numbers = generate_numbers_list(clean_prefix, 3)

        num_text = "\n".join([f"📱 `{num}`" for num in numbers])

        header_text = f"❓ Service: 📘 Facebook\n{country_display}\n\n{num_text}\n\n⏳ Waiting for OTP..."
        reply_markup = create_multi_number_markup(numbers)
        await query.edit_message_text(header_text, reply_markup=reply_markup, parse_mode="Markdown")

    elif query.data == "change_country":
        await query.answer("Country list will be updated soon!", show_alert=True)
        
    elif query.data == "withdraw_binance":
        await query.answer("Minimum withdraw is $0.2", show_alert=True)
        
    elif query.data == "set_binance":
        await query.message.reply_text("Please send your Binance Pay ID:")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading

    class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running!")

    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    app.run_polling()
