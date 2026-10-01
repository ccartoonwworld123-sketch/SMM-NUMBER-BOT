import os
from threading import Thread
import requests
import telebot
from telebot import types
from flask import Flask

# =========================================================
# CONFIG & CREDENTIALS
# =========================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8752686767:AAEKH4RRI6jWzinLnpDEdah-OtWhG4h-Bb0")
VOLTX_API_KEY = "MHPU3S5IV1A"
OTP_GROUP_CHAT_ID = "-1004436883235"
OTP_GROUP_LINK = "https://t.me/smm_otp_grup"

# Mandatory Channel for Subscription Check
REQUIRED_CHANNEL = "@A_ToolsX"  # অথবা চ্যানেলের চ্যাট আইডি/ইউজারনেম
CHANNEL_INVITE_LINK = "https://t.me/A_ToolsX"

# Voltx API Base Path
BASE_API_URL = "https://api.2oo9.cloud/MXS47FLFXOU/tnevs/@public/api"
HEADERS = {
    "mauthapi": VOLTX_API_KEY,
    "Authorization": f"Bearer {VOLTX_API_KEY}",
    "Accept": "application/json"
}

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# =========================================================
# USER DATA & MEMBERSHIP CHECK
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

def is_member(user_id):
    try:
        member = bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        # যদি মেম্বারশিপ status এগুলো হয় তবে সে জয়েন করেছে
        if member.status in ["member", "administrator", "creator"]:
            return True
    except Exception as e:
        print(f"Membership Check Error: {e}")
    return False

def send_subscription_required(chat_id):
    text = (
        "🚀 <b>To use this bot, you must join our channel:</b>\n"
        f"🔗 {CHANNEL_INVITE_LINK}"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "📢 VIEW CHANNEL",
            url=CHANNEL_INVITE_LINK
        )
    )
    bot.send_message(chat_id, text, reply_markup=markup)

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
    user_id = message.from_user.id

    if not is_member(user_id):
        send_subscription_required(message.chat.id)
        return

    user = get_user(user_id)

    text = (
        "👋 <b>Welcome to FB MASTER NUMBER</b>\n\n"
        f"💰 <b>Current Balance:</b> ${user['balance']:.3f}\n"
        f"🆔 <b>Binance Pay ID:</b> {user['binance_id']}\n\n"
        "<i>Minimum withdraw is $0.2</i>"
    )

    inline = types.InlineKeyboardMarkup(row_width=1)
    inline.add(
        types.InlineKeyboardButton(
            "💳 Withdraw via Binance",
            callback_data="withdraw"
        )
    )
    inline.add(
        types.InlineKeyboardButton(
            "🔴 Set Binance ID",
            callback_data="set_binance"
        )
    )
    inline.add(
        types.InlineKeyboardButton(
            "📣 OTP Group ↗",
            callback_data="otp_group"
        )
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=inline
    )
    bot.send_message(
        message.chat.id,
        "👇 <b>Main Menu</b>",
        reply_markup=main_menu()
    )


# =========================================================
# OTP GROUP
# =========================================================
@bot.message_handler(func=lambda m: m.text == "📣 OTP Group")
def otp_group_button(message):
    if not is_member(message.from_user.id):
        send_subscription_required(message.chat.id)
        return
    send_otp_group(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "otp_group")
def otp_group_callback(call):
    if not is_member(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Please join the channel first!", show_alert=True)
        send_subscription_required(call.message.chat.id)
        return
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
    if not is_member(message.from_user.id):
        send_subscription_required(message.chat.id)
        return

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
    if not is_member(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Please join the channel first!", show_alert=True)
        send_subscription_required(call.message.chat.id)
        return

    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        call.message.chat.id,
        "🆔 <b>Send your Binance Pay ID:</b>"
    )
    bot.register_next_step_handler(msg, save_binance_id)

def save_binance_id(message):
    if not is_member(message.from_user.id):
        send_subscription_required(message.chat.id)
        return

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
    if not is_member(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Please join the channel first!", show_alert=True)
        send_subscription_required(call.message.chat.id)
        return

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
    if not is_member(message.from_user.id):
        send_subscription_required(message.chat.id)
        return

    msg = bot.send_message(
        message.chat.id,
        "⚙️ <b>Send your range:</b>\n\n"
        "Example:\n"
        "<code>22896</code>"
    )
    bot.register_next_step_handler(msg, save_range)

def save_range(message):
    if not is_member(message.from_user.id):
        send_subscription_required(message.chat.id)
        return

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
    if not is_member(message.from_user.id):
        send_subscription_required(message.chat.id)
        return

    user = get_user(message.from_user.id)

    text = (
        "🌐 <b>Country:</b> Togo 🇹🇬\n"
        f"⚙️ <b>Range:</b> {user['range']}\n\n"
        "📱 <b>Available Numbers</b>"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("+22896234416", callback_data="number_1"))
    markup.add(types.InlineKeyboardButton("+22896161787", callback_data="number_2"))
    markup.add(types.InlineKeyboardButton("🔄 Change Number", callback_data="change_number"))

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=markup
    )


# =========================================================
# NUMBER BUTTONS & CHANGE NUMBER
# =========================================================
@bot.callback_query_handler(func=lambda call: call.data in ["number_1", "number_2"])
def number_selected(call):
    if not is_member(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Please join the channel first!", show_alert=True)
        send_subscription_required(call.message.chat.id)
        return
    bot.answer_callback_query(call.id, "Number selected.")

@bot.callback_query_handler(func=lambda call: call.data == "change_number")
def change_number(call):
    if not is_member(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Please join the channel first!", show_alert=True)
        send_subscription_required(call.message.chat.id)
        return
    bot.answer_callback_query(call.id, "Number changed.")
    bot.send_message(
        call.message.chat.id,
        "🔄 <b>Number list refreshed.</b>"
    )


# =========================================================
# LIVE TRAFFIC
# =========================================================
@bot.message_handler(func=lambda m: m.text == "🟢 Live Traffic")
def live_traffic(message):
    if not is_member(message.from_user.id):
        send_subscription_required(message.chat.id)
        return

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
                    otp_id = otp.get("otp_id") or otp.get("time") or otp.get("number") or str(otp)
                    if otp_id not in sent_ids:
                        sent_ids.add(otp_id)
                        if len(sent_ids) > 100:
                            sent_ids.pop()
                            
                        service = otp.get("source", otp.get("service", "FB"))
                        message_text = otp.get("message", "Facebook: Your code is 240022")
                        country = otp.get("country", "Togo")
                        range_val = otp.get("range", "22896")
                        
                        formatted_msg = (
                            f"🟢 <b>OTP RECEIVED</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━\n"
                            f"🌐 <b>Country</b> : {country}\n"
                            f"🎯 <b>Range</b>   : {range_val}\n"
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
        app.run(host="0.0.0.0", port=8080)

    Thread(target=run_flask, daemon=True).start()
    Thread(target=background_otp_worker, daemon=True).start()

    print("🤖 Bot and Web Server are running...")
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True, interval=1, timeout=20)
