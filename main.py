import os
import requests
import telebot

from flask import Flask
from threading import Thread
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

OTP_GROUP_LINK = "https://t.me/smm_otp_grup"


# =========================================================
# VALIDATE CONFIG
# =========================================================

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing.")

if not VOLTX_API_KEY:
    raise RuntimeError("VOLTX_API_KEY environment variable is missing.")


# =========================================================
# API CONFIG
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
# USER DATA
# =========================================================

users = {}


def get_user(user_id):
    if user_id not in users:
        users[user_id] = {
            "balance": 0.091,
            "binance_id": "Not Set",
            "range": "22897",
        }

    return users[user_id]


# =========================================================
# VOLTX API REQUEST HELPER
# =========================================================

def api_request(method, endpoint, **kwargs):
    url = f"{BASE_API_URL}/{endpoint.lstrip('/')}"

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=API_HEADERS,
            timeout=15,
            **kwargs
        )

        print("API:", method, url)
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text[:2000])

        try:
            data = response.json()
        except ValueError:
            return None, "API returned invalid JSON."

        if response.status_code != 200:
            return None, (
                f"HTTP {response.status_code}: "
                f"{data.get('message', 'API request failed')}"
            )

        return data, None

    except requests.RequestException as e:
        print("API CONNECTION ERROR:", e)
        return None, f"Connection error: {e}"


# =========================================================
# GET REAL NUMBER
# =========================================================

def get_real_number(range_value):
    """
    VoltX documentation:

    POST /getnum

    Body:
    {
        "rid": "22897"
    }
    """

    payload = {
        "rid": str(range_value)
    }

    data, error = api_request(
        "POST",
        "/getnum",
        json=payload
    )

    if error:
        return None, error

    if not data:
        return None, "Empty API response."

    meta = data.get("meta", {})

    if meta.get("code") != 200:
        return None, data.get(
            "message",
            "Number could not be allocated."
        )

    number_data = data.get("data") or {}

    full_number = number_data.get("full_number")

    if not full_number:
        return None, "API did not return a number."

    return full_number, None


# =========================================================
# LIVE ACCESS
# =========================================================

def get_live_access():
    """
    GET /liveaccess
    """

    data, error = api_request(
        "GET",
        "/liveaccess"
    )

    if error:
        return None, error

    if not data:
        return None, "Empty API response."

    if data.get("meta", {}).get("code") != 200:
        return None, data.get(
            "message",
            "Unable to get live access."
        )

    return data.get("data", {}), None


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

    get_user(message.from_user.id)

    text = (
        "👋 <b>Welcome to FB MASTER NUMBER</b>\n\n"
        "Please choose an option from the menu below:"
    )

    bot.send_message(
        message.chat.id,
        text,
        reply_markup=main_menu()
    )


# =========================================================
# OTP GROUP BUTTON
# =========================================================

@bot.message_handler(
    func=lambda message:
    message.text == "📣 OTP Group"
)
def otp_group_button(message):

    markup = types.InlineKeyboardMarkup()

    markup.add(
        types.InlineKeyboardButton(
            "📣 Join Group ↗",
            url=OTP_GROUP_LINK
        )
    )

    bot.send_message(
        message.chat.id,
        "📣 <b>Official Group</b>\n\n"
        "Join our group for updates:",
        reply_markup=markup
    )


# =========================================================
# BALANCE
# =========================================================

@bot.message_handler(
    func=lambda message:
    message.text == "💳 Balance"
)
def balance(message):

    user = get_user(message.from_user.id)

    text = (
        f"💰 <b>Current Balance:</b> "
        f"${user['balance']:.3f}\n"
        f"🆔 <b>Binance Pay ID:</b> "
        f"{user['binance_id']}\n\n"
        "Minimum withdraw: <b>$0.2</b>"
    )

    markup = types.InlineKeyboardMarkup(
        row_width=1
    )

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

@bot.callback_query_handler(
    func=lambda call:
    call.data == "set_binance"
)
def set_binance(call):

    bot.answer_callback_query(call.id)

    msg = bot.send_message(
        call.message.chat.id,
        "🆔 <b>Send your Binance Pay ID:</b>"
    )

    bot.register_next_step_handler(
        msg,
        save_binance_id
    )


def save_binance_id(message):

    if not message.text:
        bot.send_message(
            message.chat.id,
            "❌ Invalid Binance Pay ID.",
            reply_markup=main_menu()
        )
        return

    user = get_user(message.from_user.id)

    user["binance_id"] = message.text.strip()

    bot.send_message(
        message.chat.id,
        "✅ <b>Binance Pay ID saved.</b>",
        reply_markup=main_menu()
    )


# =========================================================
# WITHDRAW
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "withdraw"
)
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
            "❌ Set Binance Pay ID first.",
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

@bot.message_handler(
    func=lambda message:
    message.text == "⚙️ Set Range"
)
def set_range(message):

    msg = bot.send_message(
        message.chat.id,
        "⚙️ <b>Send your range:</b>\n\n"
        "Example:\n"
        "<code>22897</code>\n\n"
        "Do not include XXX."
    )

    bot.register_next_step_handler(
        msg,
        save_range
    )


def save_range(message):

    value = (message.text or "").strip()

    # Only digits
    if not value.isdigit():

        bot.send_message(
            message.chat.id,
            "❌ Range must contain digits only.",
            reply_markup=main_menu()
        )

        return

    user = get_user(message.from_user.id)

    user["range"] = value

    bot.send_message(
        message.chat.id,
        f"✅ <b>Range saved:</b> "
        f"<code>{value}</code>",
        reply_markup=main_menu()
    )


# =========================================================
# NUMBER MESSAGE
# =========================================================

def send_number_message(chat_id, range_value, number):

    text = (
        "🌐 <b>Country :</b> Togo 🇹🇬\n"
        f"⚙️ <b>Range   :</b> <code>{range_value}</code>\n\n"
        f"📞 <b>Number :</b> <code>{number}</code>"
    )

    markup = types.InlineKeyboardMarkup(
        row_width=1
    )

    # Telegram copy button
    try:

        markup.add(
            types.InlineKeyboardButton(
                f"📋 {number}",
                copy_text=types.CopyTextButton(number)
            )
        )

    except Exception:

        # Fallback for old pyTelegramBotAPI
        markup.add(
            types.InlineKeyboardButton(
                f"📋 {number}",
                callback_data="copy_unavailable"
            )
        )

    markup.add(
        types.InlineKeyboardButton(
            "🔄 Change Number",
            callback_data="change_number"
        )
    )

    bot.send_message(
        chat_id,
        text,
        reply_markup=markup
    )


# =========================================================
# GET API NUMBER
# =========================================================

@bot.message_handler(
    func=lambda message:
    message.text == "📞 Get API Number"
)
def get_api_number(message):

    user = get_user(message.from_user.id)

    range_value = user["range"]

    # Show waiting message
    wait_msg = bot.send_message(
        message.chat.id,
        "⏳ <b>Requesting a real number from panel...</b>"
    )

    number, error = get_real_number(
        range_value
    )

    if not number:

        bot.edit_message_text(
            "❌ <b>Number unavailable</b>\n\n"
            f"⚙️ Range: <code>{range_value}</code>\n"
            f"⚠️ {error}",
            message.chat.id,
            wait_msg.message_id
        )

        return

    # Delete waiting message
    try:
        bot.delete_message(
            message.chat.id,
            wait_msg.message_id
        )
    except Exception:
        pass

    send_number_message(
        message.chat.id,
        range_value,
        number
    )


# =========================================================
# CHANGE NUMBER
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "change_number"
)
def change_number(call):

    bot.answer_callback_query(
        call.id,
        "Requesting new number..."
    )

    user = get_user(call.from_user.id)

    range_value = user["range"]

    number, error = get_real_number(
        range_value
    )

    if not number:

        bot.send_message(
            call.message.chat.id,
            "❌ <b>Could not get a new number.</b>\n\n"
            f"⚙️ Range: <code>{range_value}</code>\n"
            f"⚠️ {error}"
        )

        return

    text = (
        "🌐 <b>Country :</b> Togo 🇹🇬\n"
        f"⚙️ <b>Range   :</b> <code>{range_value}</code>\n\n"
        f"📞 <b>Number :</b> <code>{number}</code>"
    )

    markup = types.InlineKeyboardMarkup(
        row_width=1
    )

    try:

        markup.add(
            types.InlineKeyboardButton(
                f"📋 {number}",
                copy_text=types.CopyTextButton(number)
            )
        )

    except Exception:

        pass

    markup.add(
        types.InlineKeyboardButton(
            "🔄 Change Number",
            callback_data="change_number"
        )
    )

    try:

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
            parse_mode="HTML"
        )

    except Exception as e:

        print("Edit message error:", e)

        bot.send_message(
            call.message.chat.id,
            text,
            reply_markup=markup
        )


# =========================================================
# COPY FALLBACK
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
    call.data == "copy_unavailable"
)
def copy_unavailable(call):

    bot.answer_callback_query(
        call.id,
        "Long press the number to copy.",
        show_alert=True
    )


# =========================================================
# LIVE TRAFFIC / LIVE ACCESS
# =========================================================

@bot.message_handler(
    func=lambda message:
    message.text == "🟢 Live Traffic"
)
def live_traffic(message):

    data, error = get_live_access()

    if error:

        bot.send_message(
            message.chat.id,
            "❌ <b>Live data unavailable</b>\n\n"
            f"⚠️ {error}"
        )

        return

    services = data.get("services", [])

    if not services:

        bot.send_message(
            message.chat.id,
            "🟢 <b>Live Access</b>\n\n"
            "No active services returned by panel."
        )

        return

    lines = [
        "🟢 <b>Live Traffic</b>",
        ""
    ]

    for service in services:

        sid = service.get("sid", "Unknown")
        last_at = service.get("last_at", "N/A")
        ranges = service.get("ranges", [])

        lines.append(
            f"📱 <b>Service:</b> {sid}"
        )

        lines.append(
            f"🕐 <b>Last:</b> {last_at}"
        )

        if ranges:

            lines.append(
                "⚙️ <b>Ranges:</b>"
            )

            for r in ranges:

                lines.append(
                    f"• <code>{r}</code>"
                )

        lines.append("")

    bot.send_message(
        message.chat.id,
        "\n".join(lines)
    )


# =========================================================
# UNKNOWN CALLBACK
# =========================================================

@bot.callback_query_handler(
    func=lambda call: True
)
def unknown_callback(call):

    try:
        bot.answer_callback_query(
            call.id
        )
    except Exception:
        pass


# =========================================================
# FLASK
# =========================================================

@app.route("/")
def home():

    return "VoltX API Telegram Bot is running."


@app.route("/health")
def health():

    return {
        "status": "ok",
        "bot": "running"
    }


# =========================================================
# FLASK THREAD
# =========================================================

def run_flask():

    app.run(
        host="0.0.0.0",
        port=int(
            os.getenv("PORT", "8080")
        )
    )


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    Thread(
        target=run_flask,
        daemon=True
    ).start()

    print("================================")
    print("VoltX Telegram Bot")
    print("API:", BASE_API_URL)
    print("================================")

    bot.remove_webhook()

    bot.infinity_polling(
        skip_pending=True,
        interval=1,
        timeout=30,
        long_polling_timeout=30
    )
