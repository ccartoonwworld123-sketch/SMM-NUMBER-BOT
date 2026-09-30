import os
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Voltx Panel API Credentials
VOLTX_API_KEY = "MHPU3S5IV1A"
VOLTX_API_URL = "https://voltxsms.com/stubs/handler_api.php"  # Standard Voltx Stubs Endpoint
YOUR_TELEGRAM_USERNAME = "smmsaport"

USER_STATES = {}

def get_voltx_number(service="fb", country="ci"):
    """
    Voltx API থেকে আসল লাইভ নম্বর কেনা এবং Order ID নেওয়ার ফাংশন
    """
    params = {
        "api_key": VOLTX_API_KEY,
        "action": "getNumber",
        "service": service,
        "country": country
    }
    try:
        response = requests.get(VOLTX_API_URL, params=params, timeout=12)
        # Response Format Example: ACCESS_NUMBER:12345678:2250700000000
        text = response.text.strip()
        if text.startswith("ACCESS_NUMBER"):
            parts = text.split(":")
            order_id = parts[1]
            phone_number = "+" + parts[2]
            return phone_number, order_id
        else:
            print(f"Voltx Response Message: {text}")
    except Exception as e:
        print(f"Voltx Get Number Error: {e}")
        
    return None, None

def check_voltx_otp(order_id):
    """
    Voltx API থেকে OTP এসেছে কিনা চেক করার ফাংশন
    """
    params = {
        "api_key": VOLTX_API_KEY,
        "action": "getStatus",
        "id": order_id
    }
    try:
        response = requests.get(VOLTX_API_URL, params=params, timeout=10)
        text = response.text.strip()
        # Response Format Example: STATUS_OK:123456
        if text.startswith("STATUS_OK"):
            otp_code = text.split(":")[1]
            return otp_code
        elif text == "STATUS_WAIT_CODE":
            return "WAITING"
    except Exception as e:
        print(f"Voltx Check OTP Error: {e}")
        
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
    
    welcome_text = "Welcome to FB MASTER NUMBER bot! 🤖\nPlease select an option from the menu below:"
    await update.message.reply_text(welcome_text, reply_markup=markup)

async def poll_for_otp(chat_id, order_id, phone, context):
    """
    ব্যাকগ্রাউন্ডে ২ মিনিট ধরে প্রতি ৫ সেকেন্ড পর পর OTP চেক করার লুপ
    """
    max_attempts = 24  # 5 সেকেন্ড x 24 বার = 120 সেকেন্ড (2 মিনিট)
    for _ in range(max_attempts):
        await asyncio.sleep(5)
        status = check_voltx_otp(order_id)
        if status and status != "WAITING":
            otp_message = (
                f"✅ **Facebook OTP Received!**\n\n"
                f"📱 **Number:** `{phone}`\n"
                f"🔑 **OTP Code:** `{status}`"
            )
            await context.bot.send_message(chat_id=chat_id, text=otp_message, parse_mode="Markdown")
            return
            
    await context.bot.send_message(chat_id=chat_id, text=f"⚠️ Timeout! No OTP received for `{phone}`.", parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Target Range handling
    if USER_STATES.get(user_id) == "WAITING_FOR_RANGE":
        if "x" in text.lower() or text.isdigit():
            USER_STATES[user_id] = None
            await update.message.reply_text(f"🔴 Target range updated to: `{text}`", parse_mode="Markdown")
        else:
            await update.message.reply_text("🔴 Invalid range! Please enter a valid number prefix (e.g. 5198xxxxxx or 1234xxxx).")
        return

    if text == "📞 Get API Number":
        await update.message.reply_text("⏳ Fetching live Facebook number from Voltx Panel...")
        phone, order_id = get_voltx_number(service="fb", country="ci")
        
        if phone and order_id:
            header_text = f"❓ Service: 📘 Facebook\n🇨🇮 Country: IVORY COAST (CI)\n📱 Number: `{phone}`\n\n⏳ Waiting for OTP..."
            reply_markup = create_number_markup(phone)
            await update.message.reply_text(header_text, reply_markup=reply_markup, parse_mode="Markdown")
            
            # Start background listener for OTP
            asyncio.create_task(poll_for_otp(update.effective_chat.id, order_id, phone, context))
        else:
            await update.message.reply_text("⚠️ Failed to fetch number from Voltx Panel! Please check your panel balance or try again in a few seconds.")

    elif text == "⚙️ Set Range":
        USER_STATES[user_id] = "WAITING_FOR_RANGE"
        await update.message.reply_text("🔴 Please send your target number range (e.g. 5198xxxxxx or 1234xxxx):")

    elif text == "🟢 Live Traffic":
        traffic_msg = (
            "📊 **LIVE TRAFFIC STATUS**\n\n"
            "🟢 🇨🇮 Ivory Coast (CI) - HIGH (Fast OTP)\n"
            "🟢 🇮🇩 Indonesia (ID) - MEDIUM\n"
            "🟡 🇵🇭 Philippines (PH) - NORMAL\n\n"
            "⚡ Best Server Right Now: **Ivory Coast (CI)**"
        )
        await update.message.reply_text(traffic_msg, parse_mode="Markdown")

    elif text == "💳 Balance":
        balance_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Withdraw via Binance", callback_data="withdraw_binance")],
            [InlineKeyboardButton("🔴 Set Binance ID", callback_data="set_binance")],
            [InlineKeyboardButton("📣 OTP Group ↗️", url=f"https://t.me/{YOUR_TELEGRAM_USERNAME}")]
        ])
        
        balance_text = (
            "Current Balance: $0.091\n"
            "Binance Pay ID: Not Set\n\n"
            "Minimum withdraw is $0.2"
        )
        await update.message.reply_text(balance_text, reply_markup=balance_markup)

    elif text == "📣 OTP Group":
        await update.message.reply_text(f"📣 Join our OTP Group: t.me/{YOUR_TELEGRAM_USERNAME}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "change_number":
        await query.message.reply_text("⏳ Fetching new Facebook number...")
        phone, order_id = get_voltx_number(service="fb", country="ci")
        
        if phone and order_id:
            header_text = f"❓ Service: 📘 Facebook\n🇨🇮 Country: IVORY COAST (CI)\n📱 Number: `{phone}`\n\n⏳ Waiting for OTP..."
            reply_markup = create_number_markup(phone)
            await query.edit_message_text(header_text, reply_markup=reply_markup, parse_mode="Markdown")
            
            asyncio.create_task(poll_for_otp(query.message.chat_id, order_id, phone, context))
        else:
            await query.message.reply_text("⚠️ Unable to fetch new number from Voltx Panel right now. Please try again.")

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

    # Dummy HTTP server for Render port binding
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
