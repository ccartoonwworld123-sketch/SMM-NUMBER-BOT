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
    "mauthapi": VOLTX_API_KEY,
    "Authorization": f"Bearer {VOLTX_API_KEY}",
    "Content-Type": "application/json"
}

# Initialize Telegram Bot & Flask App
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

@app.route("/")
def home():
    return "FB MASTER NUMBER Bot is active and running!"

# --- Debug API Functions ---
def fetch_recent_otps():
    url = f"{BASE_API_URL}/success-otp"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        print(f"API Response Code: {response.status_code}")
        print(f"API Response Body: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return data
            return data.get("data", {}).get("otps", data.get("otps", []))
    except Exception as e:
        print(f"Error fetching OTPs: {e}")
    return []

# --- Formatting OTP ---
def format_otp_message(otp_item):
    service = otp_item.get("service", otp_item.get("sid", "FACEBOOK"))
    number = otp_item.get("number", "xxxxxxx")
    message_text = otp_item.get("message", "No message content")
    time_str = otp_item.get("time", "")
    operator = otp_item.get("operator", "MOBILE")
    country = otp_item.get("country", "")

    formatted_msg = (
        f"🔹 **{service}**  `{number}`\n"
        f"💬 {message_text}\n"
    )
    if time_str or country:
        formatted_msg += f"🕒 `{time_str}`  |  🌐 *{operator}* {country}"
        
    return formatted_msg

# --- Background Worker ---
def background_relay_worker():
    last_seen_otp_id = None
    while True:
        try:
            otps = fetch_recent_otps()
            if otps and isinstance(otps, list):
                latest = otps[0]
                otp_id = latest.get("otp_id") or latest.get("time") or latest.get("number")
                
                if otp_id != last_seen_otp_id:
                    last_seen_otp_id = otp_id
                    formatted_msg = format_otp_message(latest)
                    bot.send_message(OTP_GROUP_CHAT_ID, formatted_msg, parse_mode="Markdown")
                    print("OTP successfully sent to group!")
        except Exception as e:
            print(f"Background worker error: {e}")
        
        time.sleep(5)

# --- Main Execution ---
if __name__ == "__main__":
    print("Starting Flask, Bot, and Debug Background Worker...")
    
    def run_flask():
        app.run(host="0.0.0.0", port=8080)
    Thread(target=run_flask, daemon=True).start()
    
    Thread(target=background_relay_worker, daemon=True).start()
    
    bot.infinity_polling()
