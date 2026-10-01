import os
import time
import threading
import requests
import telebot

from flask import Flask, jsonify
from telebot import types


# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
VOLTX_API_KEY = os.getenv("VOLTX_API_KEY")

BASE_API_URL = (
    "https://api.2009.cloud/"
    "MXS47FLFX0/tnevs/@public/api"
)

REQUEST_TIMEOUT = 20


# =========================================================
# ENV CHECK
# =========================================================

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

if not VOLTX_API_KEY:
    raise RuntimeError("VOLTX_API_KEY is missing")


# =========================================================
# API HEADERS
# =========================================================

API_HEADERS = {
    "mauthapi": VOLTX_API_KEY,
    "Accept": "application/json",
    "Content-Type": "application/json",
}


# =========================================================
# BOT / FLASK
# =========================================================

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)

app = Flask(__name__)


# =========================================================
# MEMORY DATA
# =========================================================

users = {}


def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "balance": 0.091,
            "binance_id": "Not Set",
        }

    return users[user_id]


# =========================================================
# API REQUEST
# =========================================================

def api_request(method, endpoint, **kwargs):

    url = f"{BASE_API_URL.rstrip('/')}/{endpoint.lstrip('/')}"

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=API_HEADERS,
            timeout=REQUEST_TIMEOUT,
            **kwargs
        )

        print("=" * 60)
        print("API REQUEST")
        print("METHOD :", method)
        print("URL    :", url)
        print("STATUS :", response.status_code)
        print("BODY   :", response.text[:2000])
        print("=" * 60)

        response.raise_for_status()

        try:
            return response.json()

        except ValueError:
            return {
                "ok": False,
                "error": "API returned invalid JSON"
            }

    except requests.exceptions.Timeout:
        return {
            "ok": False,
            "error": "API request timed out"
        }

    except requests.exceptions.ConnectionError:
        return {
            "ok": False,
            "error": "Could not connect to API"
        }

    except requests.exceptions.HTTPError as e:
        return {
            "ok": False,
            "error": f"HTTP error: {e}"
        }

    except requests.exceptions.RequestException as e:
        return {
            "ok": False,
            "error": str(e)
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


# =========================================================
# LIVE ACCESS
# =========================================================

def get_live_access():

    result = api_request(
        "GET",
        "liveaccess"
    )

    if not result.get("ok", True):
        return result

    return result


def format_live_access(data):

    if not isinstance(data, dict):
        return "❌ Invalid API response."

    meta = data.get("meta", {})

    if meta.get("code") != 200:
        return (
            "❌ <b>API Error</b>\n\n"
            f"Code: <code>{meta.get('code')}</code>\n"
            f"Status: <code>{meta.get('status')}</code>"
        )

    payload = data.get("data", {})
    services = payload.get("services", [])

    if not services:
        return (
            "🌐 <b>Live Access</b>\n\n"
            "কোনো active service পাওয়া যায়নি।"
        )

    lines = [
        "🌐 <b>Live Services</b>",
        ""
    ]

    for service in services:

        sid = service.get("sid", "Unknown")
        ranges = service.get("ranges", [])

        lines.append(
            f"📡 <b>Service:</b> <code>{sid}</code>"
        )

        if ranges:
            for r in ranges:
                lines.append(
                    f"⚙️ <code>{r}</code>"
                )
        else:
            lines.append("⚙️ No range")

        lines.append("")

    return "\n".join(lines)


# =========================================================
# KEYBOARDS
# =========================================================

def main_keyboard():

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton(
            "👤 Profile",
            callback_data="profile"
        ),
        types.InlineKeyboardButton(
            "🌐 Live Access",
            callback_data="liveaccess"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🔄 Refresh",
            callback_data="refresh"
        ),
        types.InlineKeyboardButton(
            "ℹ️ API Status",
            callback_data="api_status"
        )
    )

    return keyboard


def back_keyboard():

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "🔙 Back",
            callback_data="back"
        )
    )

    return keyboard


# =========================================================
# START
# =========================================================

@bot.message_handler(commands=["start"])
def start_handler(message):

    user = get_user(message.from_user.id)

    text = (
        "🤖 <b>Bot Online</b>\n\n"
        f"💰 Balance: <code>{user['balance']}</code>\n"
        f"💳 Binance ID: <code>{user['binance_id']}</code>\n\n"
        "নিচের menu থেকে option নির্বাচন করুন।"
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_keyboard()
    )


# =========================================================
# PROFILE
# =========================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "profile"
)
def profile_handler(call):

    user = get_user(call.from_user.id)

    text = (
        "👤 <b>Profile</b>\n\n"
        f"🆔 User ID:\n<code>{call.from_user.id}</code>\n\n"
        f"💰 Balance:\n<code>{user['balance']}</code>\n\n"
        f"💳 Binance ID:\n<code>{user['binance_id']}</code>"
    )

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_keyboard()
    )


# =========================================================
# LIVE ACCESS
# =========================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "liveaccess"
)
def liveaccess_handler(call):

    bot.answer_callback_query(
        call.id,
        "Loading..."
    )

    data = get_live_access()

    if not data.get("ok", True):
        text = (
            "🔴 <b>API Error</b>\n\n"
            f"<code>{data.get('error', 'Unknown error')}</code>"
        )
    else:
        text = format_live_access(data)

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_keyboard()
    )


# =========================================================
# REFRESH
# =========================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "refresh"
)
def refresh_handler(call):

    bot.answer_callback_query(
        call.id,
        "Refreshing..."
    )

    data = get_live_access()

    if not data.get("ok", True):
        text = (
            "🔴 <b>API Error</b>\n\n"
            f"<code>{data.get('error', 'Unknown error')}</code>"
        )
    else:
        text = format_live_access(data)

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=main_keyboard()
    )


# =========================================================
# API STATUS
# =========================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "api_status"
)
def api_status_handler(call):

    bot.answer_callback_query(
        call.id,
        "Checking API..."
    )

    data = get_live_access()

    if not data.get("ok", True):

        text = (
            "🔴 <b>API Status</b>\n\n"
            "❌ Connection failed\n\n"
            f"<code>{data.get('error')}</code>"
        )

    else:

        meta = data.get("meta", {})

        if meta.get("code") == 200:

            text = (
                "🟢 <b>API Status</b>\n\n"
                "Status: <b>ONLINE</b>\n"
                f"Code: <code>{meta.get('code')}</code>\n"
                f"API Status: <code>{meta.get('status')}</code>"
            )

        else:

            text = (
                "🟠 <b>API Status</b>\n\n"
                f"Code: <code>{meta.get('code')}</code>\n"
                f"Status: <code>{meta.get('status')}</code>"
            )

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_keyboard()
    )


# =========================================================
# BACK
# =========================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "back"
)
def back_handler(call):

    user = get_user(call.from_user.id)

    text = (
        "🤖 <b>Bot Menu</b>\n\n"
        f"💰 Balance: <code>{user['balance']}</code>\n"
        f"💳 Binance ID: <code>{user['binance_id']}</code>\n\n"
        "একটি option নির্বাচন করুন।"
    )

    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        text,
        call.message.chat.id,
        call.message.message_id,
        reply_markup=main_keyboard()
    )


# =========================================================
# UNKNOWN TEXT
# =========================================================

@bot.message_handler(
    func=lambda message: True
)
def text_handler(message):

    bot.send_message(
        message.chat.id,
        "🤖 Menu ব্যবহার করতে /start লিখুন।",
        reply_markup=main_keyboard()
    )


# =========================================================
# FLASK ROUTES
# =========================================================

@app.route("/")
def index():

    return jsonify({
        "status": "online",
        "bot": "running"
    })


@app.route("/health")
def health():

    return jsonify({
        "status": "healthy"
    })


# =========================================================
# RUN FLASK
# =========================================================

def run_flask():

    port = int(
        os.getenv("PORT", "10000")
    )

    print(
        f"Flask server starting on port {port}"
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )


# =========================================================
# RUN BOT
# =========================================================

def run_bot():

    print("Telegram bot starting...")

    while True:

        try:

            bot.remove_webhook()

            print("Bot polling started.")

            bot.infinity_polling(
                timeout=30,
                long_polling_timeout=30,
                skip_pending=True
            )

        except Exception as e:

            print("=" * 60)
            print("TELEGRAM BOT ERROR")
            print(str(e))
            print("=" * 60)

            time.sleep(5)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    print("=" * 60)
    print("APPLICATION STARTING")
    print("=" * 60)

    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )

    flask_thread.start()

    run_bot()
