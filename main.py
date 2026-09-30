import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

  def do_GET(self):
    self.send_response(200)
    self.end_headers()
    self.wfile.write(b"Bot is live!")


def run_dummy_server():
  port = int(os.environ.get("PORT", 8080))
  server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
  server.serve_forever()


threading.Thread(target=run_dummy_server, daemon=True).start()
import random
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

BOT_TOKEN = '8752686767:AAG8rwokonZyOQuK51yEeXoCWImPoEDVAiI'

# আইভরি কোস্ট (+225) নম্বরসমূহ
NUMBERS_POOL = [
    "+225025317957",
    "+225025445566",
    "+225025154510",
    "+2250721914730",
    "+2250721914731",
    "+2250721914732"
]

def get_3_numbers():
    return random.sample(NUMBERS_POOL, 3)

def create_number_markup(nums):
    inline_kb = [
        [InlineKeyboardButton(f"👤  📋 {nums[0]}", callback_data="num_1")],
        [InlineKeyboardButton(f"👤  📋 {nums[1]}", callback_data="num_2")],
        [InlineKeyboardButton(f"👤  📋 {nums[2]}", callback_data="num_3")],
        [InlineKeyboardButton("🔄 Change Number", callback_data="change_number")],
        [InlineKeyboardButton("🌐 Change Country", callback_data="change_country")],
        [InlineKeyboardButton("🔑 OTP Group ↗", url="https://t.me/telegram")]
    ]
    return InlineKeyboardMarkup(inline_kb)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📞 Get Number"), KeyboardButton("📊 Live Traffic")],
        [KeyboardButton("👤 My Profile"), KeyboardButton("🎪 Leaderboard")],
        [KeyboardButton("🔒 Support")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    msg_text = (
        f"🗿 Hello, {update.effective_user.first_name}! 👋\n\n"
        "📣 Get OTP codes instantly using virtual phone numbers — fast, reliable, global.\n\n"
        "⚡ Instant Delivery · 🌐 Global Numbers 📈\n\n"
        "🐱‍👤 Auto OTP Detection"
    )
    
    await update.message.reply_text(msg_text, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📞 Get Number":
        nums = get_3_numbers()
        header_text = "❓ Country: 🇨🇮 IVORY COAST (CI)\n⏳ Waiting for OTP"
        reply_markup = create_number_markup(nums)
        await update.message.reply_text(header_text, reply_markup=reply_markup)

    elif text == "📊 Live Traffic":
        await update.message.reply_text("📊 Live Traffic: All servers active!")

    elif text == "👤 My Profile":
        await update.message.reply_text(f"👤 Profile: {update.effective_user.first_name}\nBalance: 0.00৳")

    elif text == "🎪 Leaderboard":
        await update.message.reply_text("🎪 Leaderboard: No data yet.")

    elif text == "🔒 Support":elif text == "🔓 Support":elif text == "🔓 Support":
    await update.message.reply_text("সাপোর্টের জন্য যোগাযোগ করুন: https://t.me/smmsaport")

        await update.message.reply_text("🔒 Support: Contact Admin.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "change_number":
        nums = get_3_numbers()
        header_text = "❓ Country: 🇨🇮 IVORY COAST (CI)\n⏳ Waiting for OTP"
        reply_markup = create_number_markup(nums)
        await query.edit_message_text(header_text, reply_markup=reply_markup)

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("Bot is running...")
    app.run_polling()
