import time
import requests
import telebot
from telebot import types
from flask import Flask
from threading import Thread
import os

# --- Configuration & Credentials ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "8752686767:AAEKH4RRI6jWzinLnpDEdah-OtWhG4h-Bb0")
VOLTX_API_KEY = "MHPU3S5IV1A"
OTP_GROUP_CHAT_ID = "-1004436883235"
OTP_GROUP_LINK = "https://t.me/smm_otp_grup"

# Voltx API Base Path
BASE_API_URL = "https://api.2oo9.cloud/MXS47FLFXOU/tnevs/@public/api"
HEADERS = {
    "mauthapi": VOLTX_API_KEY,
    "Authorization": f"Bearer {VOLTX_API_KEY}",
    "Accept": "application/json"
}

# Initialize Telegram Bot & Flask App
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")
app = Flask(__name__)

def get_balance():
    try:
        response = requests.get(f"{BASE_API_URL}/balance", headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Balance Error: {e}")
    return None

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

@app.route("/")
def home():
    return "Bot is running live!"

# --- Keyboards ---
def main_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("Get API Number"),
        types.KeyboardButton("Set Range"),
        types.KeyboardButton("Live Traffic"),
        types.KeyboardButton("Balance"),
        types.KeyboardButton("OTP Group")
    )
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "💻 Programming & Development\n"
        "Tools • Resources • Services\n"
        "Everything you need in one place. ⚡\n\n"
        "Use the buttons below to control your panel:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_menu_clicks(message):
    text = message.text
    chat_id = message.chat.id

    if text == "Get API Number":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("+22896234416", callback_data="copy_num"))
        markup.add(types.InlineKeyboardButton("+22896161787", callback_data="copy_num"))
        markup.add(types.InlineKeyboardButton("🔄 Change Number", callback_data="change_num"))
        
        number_info = "🌐 Country : Togo\n⚙️ Range : 22896"
        bot.send_message(chat_id, number_info, reply_markup=markup)

    elif text == "Set Range":
        bot.send_message(chat_id, "🔴 Please send your target number range (e.g. 5198xxxxxx or 1234xxxx):")

    elif text == "Live Traffic":
        traffic_text = (
            "📊 **Live Trafic**\n\n"
            "🔥 **Total OTP:** 121\n"
            "⏱️ **Record:** Last 5 Minit\n"
            "👑 **Top Range:** 🌐 23762XXX FB\n\n"
            "🌐 **Range List**\n"
            "• 23762XXX - FB - 46\n"
            "• 237622XXX - FB - 27\n"
            "• 2246560XXX - FB - 8"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 Refresh", callback_data="refresh_traffic"))
        bot.send_message(chat_id, traffic_text, reply_markup=markup)

    elif text == "Balance":
        balance_text = (
            "💳 **Your Balance Account**\n\n"
            "Current Balance: `$0.091`\n"
            "Binance Pay ID: Not Set\n\n"
            "_Minimum withdraw is $0.2_"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💳 Withdraw via Binance", callback_data="withdraw"))
        markup.add(types.InlineKeyboardButton("🔴 Set Binance ID", callback_data="set_binance"))
        markup.add(types.InlineKeyboardButton("📢 OTP Group", url=OTP_GROUP_LINK))
        bot.send_message(chat_id, balance_text, reply_markup=markup)

    elif text == "OTP Group":
        group_text = (
            "📢 **Join our official OTP Group for live updates:**\n\n"
            f"Link: {OTP_GROUP_LINK}"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 Join OTP Group", url=OTP_GROUP_LINK))
        bot.send_message(chat_id, group_text, reply_markup=markup)

    else:
        bot.send_message(chat_id, "Please use the menu buttons below.", reply_markup=main_menu_keyboard())

# --- Background Worker for Instant OTP Relay (1s interval) ---
def background_relay_worker():
    sent_ids = set()
    time.sleep(5)
    while True:
        try:
            otps = fetch_recent_otps()
            if otps and isinstance(otps, list):
                for otp in reversed(otps[:20]):
                    otp_id = otp.get("otp_id") or otp.get("time") or otp.get("number") or str(otp)
                    
                    if otp_id not in sent_ids:
                        sent_ids.add(otp_id)
                        if len(sent_ids) > 150:
                            sent_ids.pop()
                            
                        service = otp.get("service", otp.get("sid", "FB"))
                        message_text = otp.get("message", "Facebook: Your code is 240022")
                        country = otp.get("country", "CM")
                        range_val = otp.get("range", "23762XXX")
                        lang = otp.get("language", "English")

                        formatted_msg = (
                            f"🟢 **OTP**                 `Admin`\n"
                            f"👤 **{service} OTP RECEIVE**\n"
                            f"━━━━━━━━━━━━━━━━━━━\n"
                            f"🇨🇲 **Country** : {country}\n"
                            f"🎯 **Range**   : {range_val}\n"
                            f"🗣️ **Language** : {lang}\n"
                            f"━━━━━━━━━━━━━━━━━━━\n"
                            f"✉ **Message** :\n"
                            f"{message_text}"
                        )
                        
                        markup = types.InlineKeyboardMarkup()
                        markup.add(types.InlineKeyboardButton("NUMBER BOT", url=f"https://t.me/{bot.get_me().username}"))
                        
                        bot.send_message(OTP_GROUP_CHAT_ID, formatted_msg, reply_markup=markup)
        except Exception as e:
            print(f"Worker Error: {e}")
        
        time.sleep(1)

if __name__ == "__main__":
    # Flask Server Thread
    def run_flask():
        app.run(host="0.0.0.0", port=8080)
    Thread(target=run_flask, daemon=True).start()
    
    # Background OTP Relay Thread
    Thread(target=background_relay_worker, daemon=True).start()
    
    print("Bot is starting polling...")
    bot.infinity_polling(skip_pending=True)
