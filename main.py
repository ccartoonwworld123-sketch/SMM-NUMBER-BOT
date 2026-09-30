import os
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

def get_voltx_number(service="fb", country="ci"):
    """
    VoltxSMS REST API request using Authorization Header
    """
    headers = {
        "Authorization": f"Bearer {VOLTX_API_KEY}",
        "Accept": "application/json"
    }
    
    # Try Correct Voltx Endpoint
    urls = [
        "https://voltxsms.com/api/v1/getNumber",
        "https://voltxsms.com/api/getNumber",
        "https://voltxsms.com/api/buy"
    ]
    
    params = {"service": service, "country": country}
    
    for url in urls:
        try:
            res = requests.get(url, headers=headers, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                phone = data.get("number") or data.get("phone")
                order_id = data.get("id") or data.get("order_id")
                if phone:
                    return phone, order_id, "SUCCESS"
        except Exception:
            continue

    return None, None, "API_ENDPOINT_ERROR"

def check_voltx_otp(order_id):
    headers = {
        "Authorization": f"Bearer {VOLTX_API_KEY}",
        "Accept": "application/json"
    }
    try:
        url = f"https://voltxsms.com/api/v1/getOtp?id={order_id}"
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get("sms") or data.get("code"):
                return data.get("sms") or data.get("code")
    except Exception as e:
        print(f"OTP Check Error: {e}")
    return None

def create_number_markup(num):
    keyboard = [
        [InlineKeyboardButton(f"👤 📋 {num}", callback_data=f"num_{num}")],
        [InlineKeyboardButton("🔄 Change Number", callback_data="change_number")],
        [InlineKeyboardButton("🌐 Change Country", callback_data="change_country")],
        [InlineKeyboardButton("📣 OTP Group ↗", url=f"https://t.me/{YOUR_TELEGRAM_USERNAME}")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [
        ["📞 Get API Number", "⚙️ Set Range"],
        ["🟢 Live Traffic", "💳 Balance"],
        ["📣 OTP Group"]
    ]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    await update.message.reply_text("Welcome to FB MASTER NUMBER bot! 🤖\nPlease select an option from the menu below:", reply_markup=markup)

async def poll_for_otp(chat_id, order_id, phone, context):
    for _ in range(24):
        await asyncio.sleep(5)
        status = check_voltx_otp(order_id)
        if status and status != "WAITING":
            otp_message = f"✅ **Facebook OTP Received!**\n\n📱 **Number:** `{phone}`\n🔑 **OTP Code:** `{status}`"
            await context.bot.send_message(chat_id=chat_id, text=otp_message, parse_mode="Markdown")
            return
    await context.bot.send_message(chat_id=chat_id, text=f"⚠️ Timeout! No OTP received for `{phone}`.", parse_mode="Markdown")

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
        await update.message.reply_text("⏳ Requesting number from Voltx Panel...")
        phone, order_id, status_msg = get_voltx_number(service="fb", country="ci")
        
        user_range = USER_RANGES.get(user_id, "23762")
        clean_prefix = user_range.lower().replace("x", "")
        
        if not phone:
            phone = f"+{clean_prefix}40912"
            
        header_text = f"❓ Service: 📘 Facebook\n🇨🇮 Country: IVORY COAST (CI)\n📱 Number: `{phone}`\n\n⏳ Waiting for OTP..."
        reply_markup = create_number_markup(phone)
        await update.message.reply_text(header_text, reply_markup=reply_markup, parse_mode="Markdown")
        
        if order_id:
            asyncio.create_task(poll_for_otp(update.effective_chat.id, order_id, phone, context))

    elif text == "⚙️ Set Range":
        USER_STATES[user_id] = "WAITING_FOR_RANGE"
        await update.message.reply_text("🔴 Please send your target number range (e.g. 5198xxxxxx or 1234xxxx):")

    elif text == "🟢 Live Traffic":
        traffic_lines = ["📊 **AVAILABLE RANGE TRAFFIC LIST**\n"]
        for r_code, count in LIVE_RANGES:
            traffic_lines.append(f"🌐 `{r_code}` - FB - **{count}**")
        
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
        phone, order_id, status_msg = get_voltx_number(service="fb", country="ci")
        
        user_range = USER_RANGES.get(user_id, "23762")
        clean_prefix = user_range.lower().replace("x", "")
        
        if not phone:
            phone = f"+{clean_prefix}88190"

        header_text = f"❓ Service: 📘 Facebook\n🇨🇮 Country: IVORY COAST (CI)\n📱 Number: `{phone}`\n\n⏳ Waiting for OTP..."
        reply_markup = create_number_markup(phone)
        await query.edit_message_text(header_text, reply_markup=reply_markup, parse_mode="Markdown")

        if order_id:
            asyncio.create_task(poll_for_otp(query.message.chat_id, order_id, phone, context))

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
