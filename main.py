import os
import time
import requests
import telebot
from flask import Flask
from threading import Thread

# --- Configuration & Credentials ---
BOT_TOKEN = "8752686767:AAGiwPVrhS2ghoEgCdmook8cJxLRuPo_UA0"
VOLTX_API_KEY = "MHPU3S5IV1A"
OTP_GROUP_CHAT_ID = "-1004436883235"

# Voltx API Base Path
BASE_API_URL = "https://api.2oo9.cloud/MXS47FLFXOU/tnevs/@public/api"
HEADERS = {
    "mauthapi": VOLTX_API_KEY
}

# Initialize Telegram Bot & Flask App
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "FB MASTER NUMBER Bot is active and running!"

# --- Voltx API Functions ---
def fetch_voltx_traffic():
    url = f"{BASE_API_URL}/liveaccess"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("services", [])
    except Exception as e:
        print(f"Error fetching traffic: {e}")
    return []

def fetch_recent_otps():
    url = f"{BASE_API_URL}/success-otp"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("otps", [])
    except Exception as e:
        print(f"Error fetching OTPs: {e}")
    return []

# --- Formatting OTP ---
def format_otp_message(otp_item):
    number = otp_item.get("number", "xxxx-xxxx")
    masked_number = f"{number[:3]}****{number[-3:]}" if len(str(number)) > 6 else "xxxx-xxxx"
    message_text = otp_item.get("message", "No message")
    
    return (
        f"🚨 **NEW OTP RECEIVED** 🚨\n\n"
        f"📱 **Number:** `{masked_number}`\n"
        f"💬 **Details:** {message_text}\n\n"
        f"⚡ *Powered by FB MASTER NUMBER*"
    )

# --- Telegram Handlers ---
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    welcome_text = (
        "🤖 *FB MASTER NUMBER Bot Active*\n\n"
        "Welcome to the official OTP relay and traffic management system."
    )
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    btn_get_number = telebot.types.InlineKeyboardButton("📱 Get API Number", callback_data="get_number")
    btn_otp_gc = telebot.types.InlineKeyboardButton("📢 OTP Group", url="https://t.me/smm_otp_grup")
    btn_get_range = telebot.types.InlineKeyboardButton("🟢 Live Traffic", callback_data="get_range")
    markup.add(btn_get_number, btn_otp_gc, btn_get_range)
    
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "get_range":
        bot.answer_callback_query(call.id, "Fetching live traffic ranges...")
        traffic_data = fetch_voltx_traffic()
        
        if not traffic_data:
            response_text = "📊 *Live Traffic*\n\nNo active traffic currently found."
        else:
            response_text = "📥 **Range List**\n"
            for item in traffic_data:
                # আপনার স্ক্রিনশটের মতো করে রেঞ্জ, সার্ভিস এবং কাউন্ট সাজানো হলো
                flag = item.get('flag', '🌐')
                ranges = item.get('range', item.get('ranges', 'N/A'))
                if isinstance(ranges, list):
                    ranges = ", ".join(ranges)
                service = item.get('service', item.get('sid', 'FACEBOOK'))
                count = item.get('count', item.get('total', '1'))
                
                response_text += f"• {flag} `{ranges}` - **{service}** - {count}\n"
                
        bot.send_message(call.message.chat.id, response_text, parse_mode="Markdown")
        
    elif call.data == "get_number":
        bot.answer_callback_query(call.id, "Processing number request...")
        bot.send_message(call.message.chat.id, "📱 Please use the panel to allocate numbers.")

# --- Background Worker to Auto-Relay OTPs ---
def background_relay_worker():
    last_seen_otp_id = None
    while True:
        try:
            otps = fetch_recent_otps()
            if otps:
                latest = otps[0]
                otp_id = latest.get("otp_id") or latest.get("time")
                
                if otp_id != last_seen_otp_id:
                    last_seen_otp_id = otp_id
                    formatted_msg = format_otp_message(latest)
                    bot.send_message(OTP_GROUP_CHAT_ID, formatted_msg, parse_mode="Markdown")
        except Exception as e:
            print(f"Background worker error: {e}")
        
        time.sleep(10)

# --- Main Execution ---
if __name__ == "__main__":
    print("Starting Flask, Bot, and Background Relay Worker...")
    
    def run_flask():
        app.run(host="0.0.0.0", port=8080)
    Thread(target=run_flask, daemon=True).start()
    
    Thread(target=background_relay_worker, daemon=True).start()
    
    bot.infinity_polling()
