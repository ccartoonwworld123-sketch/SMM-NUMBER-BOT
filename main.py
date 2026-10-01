import os
from threading import Thread
import requests
import telebot
from telebot import types
from flask import Flask

# =========================================================
# CONFIG & CREDENTIALS
# =========================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8752686767:AAGbez-t_ZhrsEbp79Wd1oYM4avQ9j1dP8Q")
VOLTX_API_KEY = "MHPU3S5IV1A"
OTP_GROUP_CHAT_ID = "-1004436883235"
OTP_GROUP_LINK = "https://t.me/smm_otp_grup"

# Voltx API Base Path
BASE_API_URL = "https://api.2oo9.cloud/MXS47FLFXOU/tnevs/@public/api"
HEADERS = {
    "mauthapi": VOLTX_API_KEY,
    "Authorization": f"Bearer {VOLTX_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# =========================================================
# USER DATA
# =========================================================
users = {}

def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "balance": 0.091,
            "binance_id": "Not Set",
            "range": "22896"
        }
    return users[user_id]

# =========================================================
# API FETCH FUNCTIONS
# =========================================================
def fetch_panel_number(range_val):
    url = f"{BASE_API_URL}/getnum"
    try:
        response = requests.post(url, headers=HEADERS, json={"rid": range_val}, timeout=10)
        if response.status_code == 200:
            res_data = response.json()
            data = res_data.get("data", res_data)
            if isinstance(data, list) and len(data) > 0:
                data = data[0]
            if isinstance(data, dict):
                num = data.get("full_number") or data.get("number") or data.get("no_plus_number")
                country = data.get("country", "Togo 🇹🇬")
                if num:
                    num = str(num).strip()
                    if not num.startswith("+"):
                        num = "+" + num
                    return num, country
    except Exception as e:
        print(f"Number Fetch Error: {e}")
    return None, "Togo 🇹🇬"

def fetch_recent_otps():
    url = f"{BASE_API_URL}/success-otp"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data.get("data", {}).get("otps", data.get("otps", data.get("result", [])))
    except Exception as e:
        print(f"OTP Error: {e}")
    return []

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
    markup.add(
        types.KeyboardButton("📣 OTP Group")
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
# OTP GROUP
# =========================================================
@bot.message_handler(func=lambda m: m.text == "📣 OTP Group")
def otp_group_button(message):
    send_otp_group(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "otp_group")
def otp_group_callback(call):
    bot.answer_callback_query(call.id)
    send_otp_group(call.message.chat.id)

def send_otp_group(chat_id):
    text = (
        "📣 <b>Official Group</b>\n\n"
        "Join our group for updates:\n"
        f"🔗 {OTP_GROUP_LINK}"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "📣 Join Group ↗",
            url=OTP_GROUP_LINK
        )
    )
    bot.send_message(
        chat_id,
        text,
        reply_markup=markup
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
# SET BINANCE ID
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


# =========================================================
# WITHDRAW
# =========================================================
@bot.callback_query_handler(func=lambda call: call.data == "withdraw")
def withdraw(call):
    user = get_user(call.from_user.id)

    if user["balance"] < 0.2:
        bot.answer_callback_query(
            call.id,
            "❌ Minimum withdraw is $0.2",
            show_alert=True
        )
        return

    if user["binance_id"] == "Not Set":
        bot.answer_callback_query(
            call.id,
            "❌ Please set Binance Pay ID first.",
            show_alert=True
        )
        return

    bot.answer_callback_query(
        call.id,
        "✅ Withdrawal request received.",
        show_alert=True
    )


# =========================================================
# SET RANGE
# =========================================================
@bot.message_handler(func=lambda m: m.text == "⚙️ Set Range")
def set_range(message):
    msg = bot.send_message(
        message.chat.id,
        "⚙️ <b>Send your range:</b>\n\n"
        "Example:\n"
        "<code>22896</code>"
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
# GET API NUMBER (Dynamic Panel Integration)
# =========================================================
@bot.message_handler(func=lambda m: m.text == "📞 Get API Number")
def get_api_number_handler(message):
    send_api_numbers(message.chat.id, message.from_user.id)

@bot.callback_query_handler(func=lambda call: call.data == "change_number")
def change_number_callback(call):
    bot.answer_callback_query(call.id, "Numbers refreshed.")
    send_api_numbers(call.message.chat.id, call.from_user.id, edit_message=call.message)

def send_api_numbers(chat_id, user_id, edit_message=None):
    user = get_user(user_id)
    range_val = user['range']
    numbers = []
    country = "Togo 🇹🇬"
    
    for _ in range(2):
        num, c = fetch_panel_number(range_val)
        if num and num not in numbers:
            numbers.append(num)
            country = c

    text = (
        f"🌐 <b>Country :</b> {country}\n"
        f"⚙️ <b>Range   :</b> {range_val}"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if numbers:
        for num in numbers:
            try:
                markup.add(types.InlineKeyboardButton(num, copy_text=types.CopyTextButton(num)))
            except:
                markup.add(types.InlineKeyboardButton(num, callback_data="dummy"))
    else:
        text += "\n\n⚠️ <i>No active numbers found from panel right now. Please try again or change range.</i>"

    markup.add(types.InlineKeyboardButton("🔄 Change Number", callback_data="change_number"))

    if edit_message:
        try:
            bot.edit_message_text(text, chat_id, edit_message.message_id, reply_markup=markup, parse_mode="HTML")
        except:
            bot.send_message(chat_id, text, reply_markup=markup)
    else:
        bot.send_message(chat_id, text, reply_markup=markup)


# =========================================================
# LIVE TRAFFIC
# =========================================================
@bot.message_handler(func=lambda m: m.text == "🟢 Live Traffic")
def live_traffic(message):
    text = (
        "🟢 <b>Live Traffic</b>\n\n"
        "📊 Active: 1\n"
        "📞 Requests: 121\n"
        "✅ Successful: 105\n"
        "❌ Failed: 16"
    )
    bot.send_message(
        message.chat.id,
        text
    )


# =========================================================
# BACKGROUND OTP WORKER
# =========================================================
def background_otp_worker():
    import time
    sent_ids = set()
    time.sleep(5)
    while True:
        try:
            otps = fetch_recent_otps()
            if otps and isinstance(otps, list):
                for otp in reversed(otps[:10]):
                    otp_id = str(otp.get("otp_id") or otp.get("id") or otp)
                    if otp_id not in sent_ids:
                        sent_ids.add(otp_id)
                        if len(sent_ids) > 100:
                            sent_ids.pop()
                            
                        number = otp.get("number", "N/A")
                        message_text = otp.get("message", "No message")
                        country = otp.get("country", "Togo 🇹🇬")
                        
                        formatted_msg = (
                            f"🟢 <b>OTP RECEIVED</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━\n"
                            f"📞 <b>Number</b> : {number}\n"
                            f"✉ <b>Message</b> :\n{message_text}"
                        )
                        markup = types.InlineKeyboardMarkup()
                        markup.add(types.InlineKeyboardButton("NUMBER BOT", url=f"https://t.me/{bot.get_me().username}"))
                        bot.send_message(OTP_GROUP_CHAT_ID, formatted_msg, reply_markup=markup)
        except Exception as e:
            print(f"Worker Error: {e}")
        time.sleep(5)


# =========================================================
# FLASK
# =========================================================
@app.route("/")
def home():
    return "Bot is running live!"


# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    def run_flask():
        port = int(os.environ.get("PORT", 8080))
        app.run(host="0.0.0.0", port=port)

    Thread(target=run_flask, daemon=True).start()
    Thread(target=background_otp_worker, daemon=True).start()

    print("🤖 Bot and Web Server are running...")
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True, interval=1, timeout=20)
