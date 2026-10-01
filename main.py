import os
import requests
import telebot
from flask import Flask
from threading import Thread

# --- Configuration & Credentials ---
BOT_TOKEN = "8752686767:AAGiwPVrhS2ghoEgCdmook8cJxLRuPo_UA0"
VOLTX_API_KEY = "MHPU3S5IV1A"
OTP_GROUP_CHAT_ID = "@smm_otp_grup"

# Initialize Telegram Bot & Flask App
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "FB MASTER NUMBER Bot is active and running!"

# --- Voltx API & Traffic Metrics Logic ---
def fetch_voltx_traffic():
    """
    Voltx API থেকে লাইভ ট্রাফিক ফেচ করে এবং count এর উপর ভিত্তি করে 
    ডিসেন্ডিং (descending) অর্ডারে সর্ট করে।
    """
    url = f"https://api.voltx.example/v1/traffic?key={VOLTX_API_KEY}" # উদাহরণস্বরূপ এন্ডপইন্ট
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # ধরে নিচ্ছি ডেটা একটি লিস্ট যেখানে আইটেমগুলোতে 'range' এবং 'count' আছে
            traffic_list = data.get("traffic", [])
            # Count অনুযায়ী descending order-এ সর্ট করা
            sorted_traffic = sorted(traffic_list, key=lambda x: x.get("count", 0), reverse=True)
            return sorted_traffic
    except Exception as e:
        print(f"Error fetching Voltx traffic: {e}")
    return []

# --- Formatting Functions ---
def format_otp_message(data):
    """
    প্রফেশনাল স্ক্রিনশট-স্টাইল এবং মাস্কড নাম্বার ফরম্যাট তৈরি করে।
    """
    number = data.get("number", "xxxx-xxxx")
    masked_number = f"{number[:3]}****{number[-3:]}" if len(number) > 6 else "xxxx-xxxx"
    country_flag = data.get("flag", "🌐")
    country_name = data.get("country", "Unknown")
    range_info = data.get("range", "N/A")
    otp_code = data.get("otp", "------")
    
    message = (
        f"🚨 **NEW OTP RECEIVED** 🚨\n\n"
        f"🌍 **Country:** {country_flag} {country_name}\n"
        f"📱 **Number:** `{masked_number}`\n"
        f"📊 **Range/Lang:** {range_info}\n"
        f"🔑 **OTP Code:** `{otp_code}`\n\n"
        f"⚡ *Powered by FB MASTER NUMBER*"
    )
    return message

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
        bot.answer_callback_query(call.id, "Fetching & sorting live traffic...")
        traffic_data = fetch_voltx_traffic()
        
        if not traffic_data:
            response_text = "📊 *Live Traffic Metrics (Sorted)*\n\nNo active traffic or API connection pending."
        else:
            response_text = "📊 *Live Traffic Metrics (Sorted by Count)*\n\n"
            for item in traffic_data:
                response_text += f"• Range: {item.get('range')} | Count: {item.get('count')}\n"
                
        bot.send_message(call.message.chat.id, response_text, parse_mode="Markdown")
        
    elif call.data == "get_number":
        bot.answer_callback_query(call.id, "Processing number request...")
        bot.send_message(call.message.chat.id, "📱 Please select your desired country/range option.")

# Function to relay OTP messages directly to the management group
def relay_otp_to_group(otp_data):
    formatted_msg = format_otp_message(otp_data)
    try:
        bot.send_message(OTP_GROUP_CHAT_ID, formatted_msg, parse_mode="Markdown")
    except Exception as e:
        print(f"Failed to send OTP to group: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    print("Starting Flask server and Telegram bot...")
    
    def run_flask():
        app.run(host="0.0.0.0", port=8080)
        
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Start Telegram Bot Polling
    bot.infinity_polling()
