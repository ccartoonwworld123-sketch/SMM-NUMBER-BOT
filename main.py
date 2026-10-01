import os
import requests
import telebot
from flask import Flask
from threading import Thread

# --- Configuration & Credentials ---
BOT_TOKEN = "8752686767:AAGiwPVrhS2ghoEgCdmook8cJxLRuPo_UA0"
VOLTX_API_KEY = "MHPU3S5IV1A"
OTP_GROUP_CHAT_ID = "@smm_otp_grup"

# Voltx API Base Path from Documentation
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

# --- Voltx API & Traffic Metrics Logic ---
def fetch_voltx_traffic():
    """
    Voltx API থেকে liveaccess এন্ডপয়েন্ট ব্যবহার করে লাইভ ট্রাফিক এবং রেঞ্জ ফেচ করে।
    """
    url = f"{BASE_API_URL}/liveaccess"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # API ডকুমেন্টেশন অনুযায়ী services ডেটা পার্স করা
            services = data.get("data", {}).get("services", [])
            return services
    except Exception as e:
        print(f"Error fetching Voltx traffic: {e}")
    return []

def fetch_recent_otps():
    """
    Voltx API থেকে সফল বা সাম্প্রতিক ওটিপি ফেচ করে।
    """
    url = f"{BASE_API_URL}/success-otp"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            otps = data.get("data", {}).get("otps", [])
            return otps
    except Exception as e:
        print(f"Error fetching recent OTPs: {e}")
    return []

# --- Formatting Functions ---
def format_otp_message(otp_item):
    """
    প্রফেশনাল লেআউটে ওটিপি মেসেজ ফরম্যাট করে।
    """
    number = otp_item.get("number", "xxxx-xxxx")
    masked_number = f"{number[:3]}****{number[-3:]}" if len(str(number)) > 6 else "xxxx-xxxx"
    message_text = otp_item.get("message", "No message")
    
    formatted_msg = (
        f"🚨 **NEW OTP RECEIVED** 🚨\n\n"
        f"📱 **Number:** `{masked_number}`\n"
        f"💬 **Details:** {message_text}\n\n"
        f"⚡ *Powered by FB MASTER NUMBER*"
    )
    return formatted_msg

# --- Telegram Bot Handlers ---
@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    welcome_text = (
        "🤖 *FB MASTER NUMBER Bot Active*\n\n"
        "Welcome to the official OTP relay and traffic management system.\n"
        "Use the buttons below to check live traffic or request numbers."
    )
    
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    btn_get_number = telebot.types.InlineKeyboardButton("📱 Get Number", callback_data="get_number")
    btn_otp_gc = telebot.types.InlineKeyboardButton("💬 OTP GC", url="https://t.me/smm_otp_grup")
    btn_get_range = telebot.types.InlineKeyboardButton("📊 Get Range", callback_data="get_range")
    markup.add(btn_get_number, btn_otp_gc, btn_get_range)
    
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "get_range":
        bot.answer_callback_query(call.id, "Fetching live traffic ranges...")
        traffic_data = fetch_voltx_traffic()
        
        if not traffic_data:
            response_text = "📊 *Live Traffic Metrics*\n\nNo active traffic currently found."
        else:
            response_text = "📊 *Live Traffic Metrics (Voltx)*\n\n"
            for item in traffic_data:
                sid = item.get('sid', 'Unknown')
                ranges = ", ".join(item.get('ranges', []))
                response_text += f"• **Service:** {sid}\n  **Ranges:** {ranges}\n\n"
                
        bot.send_message(call.message.chat.id, response_text, parse_mode="Markdown")
        
    elif call.data == "get_number":
        bot.answer_callback_query(call.id, "Processing number request...")
        bot.send_message(call.message.chat.id, "📱 Please use the panel or send request to allocate numbers.")

# Function to relay OTP messages directly to the management group
def check_and_relay_otps():
    otps = fetch_recent_otps()
    if otps:
        # Latest OTP relay logic example
        latest_otp = otps[0]
        formatted_msg = format_otp_message(latest_otp)
        try:
            bot.send_message(OTP_GROUP_CHAT_ID, formatted_msg, parse_mode="Markdown")
        except Exception as e:
            print(f"Failed to send OTP to group: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    print("Starting Flask server and Telegram bot with Voltx API integration...")
    
    def run_flask():
        app.run(host="0.0.0.0", port=8080)
        
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Start Telegram Bot Polling
    bot.infinity_polling()
