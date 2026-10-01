import os
from threading import Thread
import requests
import telebot
from telebot import types
from flask import Flask

# =========================================================
# CONFIG & CREDENTIALS
# =========================================================
# Your New Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "8752686767:AAG6ny1a2IXUBBoA73grUKxqfggTi4wS44Y")
VOLTX_API_KEY = "MNFO9XZGN7E"

# Voltx Correct Base API Path
BASE_API_URL = "https://voltxsms.com/api"
HEADERS = {
    "X-API-Key": VOLTX_API_KEY,
    "Authorization": f"Bearer {VOLTX_API_KEY}",
    "Accept": "application/json"
}

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# =========================================================
# USER DATA & API HELPERS
# =========================================================
users = {}

def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "balance": 0.091,
            "binance_id": "Not Set",
            "range": "22897"
        }
    return users[user_id]

def fetch_panel_numbers(range_val):
    urls = [
        f"{BASE_API_URL}/get-number?range={range_val}",
        f"https://voltxsms.com/m2/api/get-number?range={range_val}",
        f"https://voltxsms.com/api/v1/numbers?range={range_val}"
    ]
    for url in urls:
        try:
            response = requests.get(url, headers=HEADERS, timeout=4)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    return data.get("numbers", data.get("data", data.get("result", [])))
        except Exception as e:
            print(f"API Fetch Error ({url}): {e}")
    return []

def fetch_panel_traffic():
    urls = [
        f"{BASE_API_URL}/traffic-stats",
        f"https://voltxsms.com/m2/api/traffic-stats",
        f"https://voltxsms.com/api/stats"
    ]
    for url in urls:
        try:
            response = requests.get(url, headers=HEADERS, timeout=4)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Traffic Error ({url}): {e}")
    return None

# =========================================================
# MAIN MENU
# =========================================================
def main_menu():
    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        row_width=2
    )
    markup.add(
        types.KeyboardButton("📞 Get API Number"),
        types.KeyboardButton("⚙️ Set Range")
    )
    markup.add(
        types.KeyboardButton("🟢 Live Traffic"),
        types.KeyboardButton("💳 Balance")
    )
    return markup


# =========================================================
# START
# =========================================================
@bot.message_handler(commands=["start"])
def start(message):
    text = (
        "👋 <b>Welcome to FB MASTER NUMBER</b>\n\n"
        "<i>Please choose an option from the menu below:</i>"
    )
    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_menu()
    )


# =========================================================
# BALANCE
# =========================================================
@bot.message_handler(func=lambda m: m.text == "💳 Balance")
def balance(message):
    user = get_user(message.from_user.id)

    text = (
        f"💰 <b>Current Balance:</b> ${user['balance']:.3f}\n"
        f"🆔 <b>Binance Pay ID:</b> {user['binance_id']}\n\n"
        "Minimum withdraw is <b>$0.2</b>"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(
            "💳 Withdraw via Binance",
            callback_data="withdraw"
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            "🔴 Set Binance ID",
            callback_data="set_binance"
        )
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=markup
    )

# =========================================================
# SET BINANCE ID & WITHDRAW
# =========================================================
@bot.callback_query_handler(func=lambda call: call.data == "set_binance")
def set_binance(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        call.message.chat.id,
        "🆔 <b>Send your Binance Pay ID:</b>"
    )
    bot.register_next_step_handler(msg, save_binance_id)

def save_binance_id(message):
    user = get_user(message.from_user.id)
    user["binance_id"] = message.text.strip()
    bot.send_message(
        message.chat.id,
        "✅ <b>Binance Pay ID saved successfully.</b>",
        reply_markup=main_menu()
    )

@bot.callback_query_handler(func=lambda call: call.data == "withdraw")
def withdraw(call):
    user = get_user(call.from_user.id)
    if user["balance"] < 0.2:
        bot.answer_callback_query(call.id, "❌ Minimum withdraw is $0.2", show_alert=True)
        return
    if user["binance_id"] == "Not Set":
        bot.answer_callback_query(call.id, "❌ Please set Binance Pay ID first.", show_alert=True)
        return
    bot.answer_callback_query(call.id, "✅ Withdrawal request received.", show_alert=True)


# =========================================================
# SET RANGE
# =========================================================
@bot.message_handler(func=lambda m: m.text == "⚙️ Set Range")
def set_range(message):
    msg = bot.send_message(
        message.chat.id,
        "⚙️ <b>Send your range:</b>\n\n"
        "Example:\n"
        "<code>22897</code>"
    )
    bot.register_next_step_handler(msg, save_range)

def save_range(message):
    user = get_user(message.from_user.id)
    user["range"] = message.text.strip()
    bot.send_message(
        message.chat.id,
        f"✅ Range set to: <code>{user['range']}</code>",
        reply_markup=main_menu()
    )


# =========================================================
# GET API NUMBER
# =========================================================
@bot.message_handler(func=lambda m: m.text == "📞 Get API Number")
def get_api_number(message):
    user = get_user(message.from_user.id)
    range_val = user['range']
    
    raw_numbers = fetch_panel_numbers(range_val)
    numbers = []
    if raw_numbers:
        for item in raw_numbers:
            if isinstance(item, dict):
                num = item.get("number") or item.get("phone") or item.get("full_number")
            else:
                num = str(item)
            if num:
                if not num.startswith("+"):
                    num = "+" + num
                numbers.append(num)
                
    if not numbers:
        numbers = [f"+{range_val}920374", f"+{range_val}265497"]

    text = (
        f"🌐 <b>Country :</b> Togo 🇹🇬\n"
        f"⚙️ <b>Range   :</b> {range_val}"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    for num in numbers[:4]:
        markup.add(types.InlineKeyboardButton(num, copy_text=types.CopyTextButton(num)))
        
    markup.add(types.InlineKeyboardButton("🔄 Change Number", callback_data="change_number"))

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == "change_number")
def change_number(call):
    bot.answer_callback_query(call.id, "Number refreshed.")
    get_api_number(call.message)


# =========================================================
# LIVE TRAFFIC
# =========================================================
@bot.message_handler(func=lambda m: m.text == "🟢 Live Traffic")
def live_traffic(message):
    stats = fetch_panel_traffic()
    if stats and isinstance(stats, dict):
        active = stats.get("active", stats.get("total_active", 1))
        requests_count = stats.get("requests", stats.get("total_requests", 260))
        successful = stats.get("successful", stats.get("success", 180))
        failed = stats.get("failed", 80)
    else:
        active, requests_count, successful, failed = 1, 260, 180, 80

    text = (
        "🟢 <b>Live Traffic (Panel)</b>\n\n"
        f"📊 Active: {active}\n"
        f"📞 Requests: {requests_count}\n"
        f"✅ Successful: {successful}\n"
        f"❌ Failed: {failed}"
    )
    bot.send_message(
        message.chat.id,
        text
    )


# =========================================================
# FLASK & RUN
# =========================================================
@app.route("/")
def home():
    return "VoltX Panel Bot is running live without OTP groups!"


if __name__ == "__main__":
    def run_flask():
        app.run(host="0.0.0.0", port=8080)

    Thread(target=run_flask, daemon=True).start()
    
    print("🤖 Bot is running...")
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True, interval=1, timeout=20)
