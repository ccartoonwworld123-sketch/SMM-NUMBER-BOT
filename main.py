import os
import random
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Voltx API Configurations
VOLTX_API_KEY = "MHPU3S5IV1A"
VOLTX_BASE_URL = "https://voltxsms.com/api"  # Panel API endpoint
YOUR_TELEGRAM_USERNAME = "smmsaport"

def fetch_number_from_voltx(service="wa", country="ci"):
    """
    Voltx Panel API থেকে আসল নম্বর ও Order ID আনার ফাংশন
    """
    headers = {
        "Authorization": f"Bearer {VOLTX_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "service": service,
        "country": country
    }
    try:
        response = requests.post(f"{VOLTX_BASE_URL}/get-number", json=payload, headers=headers, timeout=10)
        data = response.json()
        if data.get("status") == "success" or data.get("success"):
            phone = data.get("phone_number") or data.get("number")
            order_id = data.get("order_id") or data.get("id")
            return phone, order_id
    except Exception as e:
        print(f"Voltx API Fetch Error: {e}")
    
    # API কানেক্ট না হওয়া পর্যন্ত ডামি নম্বর জেনারেট করবে
    return None, None

def get_3_numbers():
    numbers = []
    for _ in range(3):
        phone, _ = fetch_number_from_voltx()
        if phone:
            numbers.append(phone)
        else:
            numbers.append(f"+22507{random.randint(10000000, 99999999)}")
    return numbers

def create_number_markup(numbers):
    keyboard = []
    for num in numbers:
        keyboard.append([InlineKeyboardButton(f"👤 📋 {num}", callback_data=f"num_{num}")])
    
    keyboard.append([InlineKeyboardButton("🔄 Change Number", callback_data="change_number")])
    keyboard.append([InlineKeyboardButton("🌐 Change Country", callback_data="change_country")])
    keyboard.append([InlineKeyboardButton("🔑 OTP Group ↗️", url=f"https://t.me/{YOUR_TELEGRAM_USERNAME}")])
    
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [
        ["📞 Get Number"],
        ["📊 Live Traffic", "👤 My Profile"],
        ["🎪 Leaderboard", "🔓 Support"]
    ]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    
    welcome_text = (
        "Welcome to SMM NUMBER PANEL bot! 🤖\n\n"
        "Please select an option from the menu below:"
    )
    await update.message.reply_text(welcome_text, reply_markup=markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📞 Get Number":
        nums = get_3_numbers()
        header_text = "❓ Country: 🇨🇮 IVORY COAST (CI)\n⏳ Waiting for OTP..."
        reply_markup = create_number_markup(nums)
        await update.message.reply_text(header_text, reply_markup=reply_markup)

    elif text == "📊 Live Traffic":
        await update.message.reply_text("📊 Live Traffic: All servers active!")

    elif text == "👤 My Profile":
        await update.message.reply_text(f"👤 Profile: {update.effective_user.first_name}")

    elif text == "🎪 Leaderboard":
        await update.message.reply_text("🎪 Leaderboard: No active rankings.")

    elif text == "🔓 Support":
        support_text = f"🔓 Support: Contact Admin 👉 t.me/{YOUR_TELEGRAM_USERNAME}"
        await update.message.reply_text(support_text)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "change_number":
        nums = get_3_numbers()
        header_text = "❓ Country: 🇨🇮 IVORY COAST (CI)\n⏳ Waiting for OTP..."
        reply_markup = create_number_markup(nums)
        await query.edit_message_text(header_text, reply_markup=reply_markup)

    elif query.data == "change_country":
        await query.answer("Country list will be updated soon!", show_alert=True)

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
