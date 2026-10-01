import time
import requests
import telebot
from flask import Flask, render_template_string
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
    "Accept": "application/json"
}

# Initialize Telegram Bot & Flask App
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

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

# --- Web Panel UI ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Voltx Panel Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }
        .container { max-width: 900px; margin: auto; background: #1e293b; padding: 20px; border-radius: 10px; }
        h1 { color: #38bdf8; }
        .card { background: #334155; padding: 15px; margin: 10px 0; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚡ Voltx Instant Relay Panel</h1>
        <div class="card">
            <h3>Status: High-Speed Relay Active (1s check)</h3>
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

def format_otp_message(otp_item):
    service = otp_item.get("service", otp_item.get("sid", "FACEBOOK"))
    number = otp_item.get("number", "xxxxxxx")
    message_text = otp_item.get("message", "No message content")
    time_str = otp_item.get("time", "")
    operator = otp_item.get("operator", "MOBILE")
    country = otp_item.get("country", "")

    formatted_msg = (
        f"🔹 **NEW OTP / CODE**\n"
        f"🔹 **{service}**  `{number}`\n"
        f"💬 {message_text}\n"
    )
    if time_str or country:
        formatted_msg += f"🕒 `{time_str}`  |  🌐 *{operator}* {country}"
        
    return formatted_msg

# --- Instant Background Worker (1s interval & multi-code check) ---
def background_relay_worker():
    sent_ids = set()
    while True:
        try:
            otps = fetch_recent_otps()
            if otps and isinstance(otps, list):
                # সাম্প্রতিক কোডগুলো চেক করে যেগুলো পাঠানো হয়নি, সেগুলো সিরিয়ালের পাঠাবে
                for otp in reversed(otps[:20]):
                    otp_id = otp.get("otp_id") or otp.get("time") or otp.get("number") or str(otp)
                    
                    if otp_id not in sent_ids:
                        sent_ids.add(otp_id)
                        if len(sent_ids) > 150:
                            sent_ids.pop()
                            
                        formatted_msg = format_otp_message(otp)
                        bot.send_message(OTP_GROUP_CHAT_ID, formatted_msg, parse_mode="Markdown")
                        print("Instant OTP sent to group successfully!")
        except Exception as e:
            print(f"Worker Error: {e}")
        
        time.sleep(1) # প্রতি ১ সেকেন্ড পর পর চেক করবে

# --- Main Execution ---
if __name__ == "__main__":
    print("Starting instant panel relay system...")
    def run_flask():
        app.run(host="0.0.0.0", port=8080)
    Thread(target=run_flask, daemon=True).start()
    
    Thread(target=background_relay_worker, daemon=True).start()
    
    bot.infinity_polling()
