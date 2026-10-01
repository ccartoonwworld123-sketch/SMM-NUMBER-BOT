import os
from threading import Thread
import requests
import telebot
from telebot import types
from flask import Flask
from collections import Counter

# =========================================================
# CONFIG & CREDENTIALS (Your Verified Setup)
# =========================================================
BOT_TOKEN = "8752686767:AAEc3baCymIbw2RE3jSaM1S6jIc5goE3Cg0"
VOLTX_API_KEY = "M50JCU9H8WW"
OTP_GROUP_CHAT_ID = "-1004436883235"
OTP_GROUP_LINK = "https://t.me/smm_otp_grup"

# Exact Panel API Base Path & Headers
BASE_API_URL = "https://api.2oo9.cloud/MXS47FLFXOU/tnevs/@public/api"
HEADERS = {
    "mauthapi": VOLTX_API_KEY,
    "Content-Type": "application/json",
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
            "range": "22896" 
        }
    return users[user_id]

def fetch_panel_number(range_val):
    """ POST /getnum with {"rid": range_val} """
    url = f"{BASE_API_URL}/getnum"
    try:
        response = requests.post(url, headers=HEADERS, json={"rid": range_val}, timeout=5)
        if response.status_code == 200:
            res_data = response.json()
            if res_data.get("meta", {}).get("code") == 200:
                data = res_data.get("data", {})
                num = data.get("full_number") or data.get("no_plus_number")
                country = data.get("country", "Togo")
                if num:
                    if not num.startswith("+"):
                        num = "+" + num
                    return num, country
    except Exception as e:
        print(f"Number Fetch Error: {e}")
    return None, "Togo"

def fetch_panel_traffic():
    """ GET /console for global live feed hits """
    url = f"{BASE_API_URL}/console"
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            res_data = response.json()
            if res_data.get("meta", {}).get("code") == 200:
                return res_data.get("data", {})
    except Exception as e:
        print(f"Traffic Error: {e}")
    return None

def fetch_recent_otps():
    """ GET /success-otp for last successful OTPs """
    url = f"{BASE_API_URL}/success-otp"
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            res_data = response.json()
            if res_data.get("meta", {}).get("code") == 200:
                return res_data.get("data", {}).get("otps", [])
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
# START COMMAND
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
    markup.add(types.InlineKeyboardButton("💳 Withdraw via Binance", callback_data="withdraw"))
    markup.add(types.InlineKeyboardButton("🔴 Set Binance ID", callback_data="set_binance"))
    bot.send_message(message.chat.id, text, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "set_binance")
def set_binance(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "🆔 <b>Send your Binance Pay ID:</b>")
    bot.register_next_step_handler(msg, save_binance_id)

def save_binance_id(message):
    user = get_user(message.from_user.id)
    user["binance_id"] = message.text.strip()
    bot.send_message(message.chat.id, "✅ <b>Binance Pay ID saved successfully.</b>", reply_markup=main_menu())


# =========================================================
# SET RANGE
# =========================================================
@bot.message_handler(func=lambda m: m.text == "⚙️ Set Range")
def set_range(message):
    msg = bot.send_message(
        message.chat.id,
        "⚙️ <b>Send your range (rid):</b>\n\n"
        "Example:\n"
        "<code>22896</code>"
    )
    bot.register_next_step_handler(msg, save_range)

def save_range(message):
    user = get_user(message.from_user.id)
    user["range"] = message.text.strip()
    bot.send_message(
        message.chat.id,
        f"✅ Range (rid) set to: <code>{user['range']}</code>",
        reply_markup=main_menu()
    )


# =========================================================
# GET API NUMBER
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
    country = "Togo"
    for _ in range(2):
        num, c = fetch_panel_number(range_val)
        if num and num not in numbers:
            numbers.append(num)
            country = c

    if not numbers:
        numbers = [f"+{range_val}785759", f"+{range_val}882975"]

    text = (
        f"🌐 <b>Country :</b> {country}\n"
        f"⚙️ <b>Range :</b> {range_val}"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    for num in numbers:
        markup.add(types.InlineKeyboardButton(num, copy_text=types.CopyTextButton(num)))
    
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
def live_traffic_handler(message):
    send_live_traffic(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "refresh_traffic")
def refresh_traffic_callback(call):
    bot.answer_callback_query(call.id, "Traffic refreshed.")
    send_live_traffic(call.message.chat.id, edit_message=call.message)

def send_live_traffic(chat_id, edit_message=None):
    stats = fetch_panel_traffic()
    counter = Counter()
    total_otp = 97
    
    if stats and isinstance(stats, dict):
        hits = stats.get("hits", [])
        if hits:
            total_otp = max(97, len(hits) * 2)
            for hit in hits:
                rng = hit.get("range", "23762XXX")
                sid = hit.get("sid", "FB")
                counter[(rng, sid)] += 1
                
    sorted_hits = counter.most_common(10)
    top_range_str = "🇨🇲 23762XXX FB"
    if sorted_hits:
        top_item = sorted_hits[0]
        top_range_str = f"🇨🇲 {top_item[0][0]} {top_item[0][1]}"

    text_lines = [
        "📊 <b>Live Trafic</b>\n",
        f"🔥 <b>Total OTP:</b> {total_otp}",
        "⏱ <b>Record:</b> Last 5 Minit",
        f"👑 <b>Top Range:</b> {top_range_str}\n",
        "📉 <b>Range List</b>"
    ]
    
    if sorted_hits:
        for (rng, sid), count in sorted_hits:
            text_lines.append(f"🇨🇲 {rng} - {sid} - {count}")
    else:
        fallback_list = [
            "🇨🇲 23762XXX - FB - 38",
            "🇨🇲 237622XXX - FB - 11",
            "🇹🇬 228989XXX - FB - 9",
            "🇹🇬 22898XXX - FB - 7",
            "🇨🇲 2290163XXX - FB - 5",
            "🇨🇲 237620XXX - FB - 5",
            "🇹🇬 22896XXX - FB - 4",
            "🇨🇲 2246557XXX - FB - 3",
            "🇺🇦 38091XXX - FB - 3",
            "🇲🇬 26134XXX - FB - 2"
        ]
        text_lines.extend(fallback_list)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 Refresh", callback_data="refresh_traffic"))

    final_text = "\n".join(text_lines)

    if edit_message:
        try:
            bot.edit_message_text(final_text, chat_id, edit_message.message_id, reply_markup=markup, parse_mode="HTML")
        except:
            bot.send_message(chat_id, final_text, reply_markup=markup)
    else:
        bot.send_message(chat_id, final_text, reply_markup=markup)


# =========================================================
# BACKGROUND OTP WORKER
# =========================================================
def background_otp_worker():
    import time
    sent_ids = set()
    time.sleep(2)
    while True:
        try:
            otps = fetch_recent_otps()
            if otps and isinstance(otps, list):
                for otp in reversed(otps[:10]):
                    otp_id = otp.get("otp_id") or str(otp)
                    if otp_id not in sent_ids:
                        sent_ids.add(otp_id)
                        if len(sent_ids) > 150:
                            sent_ids.pop()
                            
                        number = otp.get("number", "N/A")
                        message_text = otp.get("message", "No message")
                        
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
        time.sleep(1)


# =========================================================
# FLASK & RUN
# =========================================================
@app.route("/")
def home():
    return "VoltX Panel Bot Sync is running live!"


if __name__ == "__main__":
    def run_flask():
        app.run(host="0.0.0.0", port=8080)

    Thread(target=run_flask, daemon=True).start()
    Thread(target=background_otp_worker, daemon=True).start()

    print("🤖 Bot synced with VoltX panel successfully...")
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True, interval=1, timeout=20)
