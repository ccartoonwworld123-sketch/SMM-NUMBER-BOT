import os
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")

VOLTX_API_KEY = "MHPU3S5IV1A"
BASE_API_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api"
YOUR_TELEGRAM_USERNAME = "smmsaport"

USER_STATES = {}
USER_RANGES = {}

def get_country_info(phone_number):
    clean_num = str(phone_number).replace("+", "").strip()
    if clean_num.startswith("237"):
        return "🇨🇲 CAMEROON (CM)", "cm"
    elif clean_num.startswith("225"):
        return "🇨🇮 IVORY COAST (CI)", "ci"
    elif clean_num.startswith("228"):
        return "🇹🇬 TOGO (TG)", "tg"
    elif clean_num.startswith("229"):
        return "🇧🇯 BENIN (BJ)", "bj"
    elif clean_num.startswith("255"):
        return "🇹🇿 TANZANIA (TZ)", "tz"
    elif clean_num.startswith("266"):
        return "🇱🇸 LESOTHO (LS)", "ls"
    else:
        return "🇨🇮 IVORY COAST (CI)", "ci"

def get_voltx_real_number(target_range="22896"):
    headers = {
        "mauthapi": VOLTX_API_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    clean_rid = str(target_range).lower().replace("x", "").strip()
    payload = {"rid": clean_rid}
    
    try:
        res = requests.post(f"{BASE_API_URL}/getnum", headers=headers, json=payload, timeout=8)
        print(f"GetNum Response: {res.status_code} | Text: {res.text}")
        if res.status_code == 200:
            res_data = res.json()
            meta = res_data.get("meta", {})
            if meta.get("code") == 200:
                data = res_data.get("data", {})
                phone = data.get("full_number") or data.get("national_number")
                # Extracting the correct unique transaction/order ID from response
                order_id = res_data.get("id") or data.get("id") or res_data.get("rid") or clean_rid
                if phone:
                    return str(phone), str(order_id)
    except Exception as e:
        print(f"API Error: {e}")

    return None, None

def fetch_live_traffic_from_panel():
    headers = {
        "mauthapi": VOLTX_API_KEY,
        "Accept": "application/json"
    }
    try:
        res = requests.get(f"{BASE_API_URL}/liveaccess", headers=headers, timeout=8)
        if res.status_code == 200:
            res_data = res.json()
            meta = res_data.get("meta", {})
            if meta.get("code") == 200:
                return res_data.get("data")
    except Exception as e:
        print(f"Live Traffic API Error: {e}")
    return None

def check_voltx_otp(order_id):
    headers = {
        "mauthapi": VOLTX_API_KEY,
        "Accept": "application/json"
    }
    
    endpoints = [
        f"{BASE_API_URL}/getotp?id={order_id}",
        f"{BASE_API_URL}/status?id={order_id}",
        f"{BASE_API_URL}/getnum?id={order_id}"
    ]
    
    for url in endpoints:
        try:
            res = requests.get(url, headers=headers, timeout=8)
            if res.status_code == 200:
                data = res.json()
                # Checking various possible keys for OTP/SMS in panel response
                sms_code = data.get("sms") or data.get("code") or data.get("otp") or data.get("text")
                if not sms_code and isinstance(data.get("data"), dict):
                    sms_code = data["data"].get("sms") or data["data"].get("code") or data["data"].get("otp")
                
                if sms_code and str(sms_code).upper() != "WAITING":
                    return str(sms_code)
        except Exception:
            continue
            
    return None

def create_multi_number_markup(numbers_list):
    keyboard = []
    for num in numbers_list:
        # Clicking this button will show a popup alert with the number for easy copying
        keyboard.append([InlineKeyboardButton(f"👤 📋 {num}", callback_data=f"copy_{num}")])
    
    keyboard.append([InlineKeyboardButton("🔄 Change Number", callback_data="change_number")])
    keyboard.append([InlineKeyboardButton("🌐 Change Country", callback_data="change_country")])
    keyboard.append([InlineKeyboardButton("📣 OTP Group ↗", url=f"https://t.me/{YOUR_TELEGRAM_USERNAME}")])
    
    return InlineKeyboardMarkup(keyboard)

async def poll_for_otp(chat_id, order_id, phone, context):
    print(f"Started polling for OTP | Order ID: {order_id} | Phone: {phone}")
    for _ in range(60): # Polling for 5 minutes (60 * 5s)
        await asyncio.sleep(5)
        status = check_voltx_otp(order_id)
        if status:
            otp_message = f"✅ **Facebook OTP Received!**\n\n📱 **Number:** `{phone}`\n🔑 **OTP Code:** `{status}`"
            await context.bot.send_message(chat_id=chat_id, text=otp_message, parse_mode="Markdown")
            return

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [
        ["📞 Get API Number", "⚙️ Set Range"],
        ["🟢 Live Traffic", "💳 Balance"],
        ["📣 OTP Group"]
    ]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    await update.message.reply_text("Welcome to FB MASTER NUMBER bot! 🤖\nPlease select an option from the menu below:", reply_markup=markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if text in ["📞 Get API Number", "⚙️ Set Range", "🟢 Live Traffic", "💳 Balance", "📣 OTP Group"]:
        USER_STATES[user_id] = None

    if USER_STATES.get(user_id) == "WAITING_FOR_RANGE":
        clean_text = text.strip()
        if "x" in clean_text.lower() or clean_text.isdigit():
            USER_STATES[user_id] = None
            USER_RANGES[user_id] = clean_text
            await update.message.reply_text(f"🔴 Target range updated to: `{clean_text}`", parse_mode="Markdown")
        else:
            await update.message.reply_text("🔴 Invalid range! Please enter a valid number prefix (e.g. 22896 or 23762).")
        return

    if text == "📞 Get API Number":
        await update.message.reply_text("⏳ Requesting real numbers from Voltx Panel...")
        
        user_range = USER_RANGES.get(user_id, "22896")
        
        numbers = []
        orders = []

        for _ in range(3):
            p, oid = get_voltx_real_number(target_range=user_range)
            if p and p not in numbers:
                numbers.append(p)
                if oid:
                    orders.append((p, oid))
            await asyncio.sleep(0.3)

        if not numbers:
            await update.message.reply_text(f"❌ **No Real Number Available!**\n\nPanel has no stock for range `{user_range}`. Check **🟢 Live Traffic** for active ranges.", parse_mode="Markdown")
            return

        num_text = "\n".join([f"📱 `{p}`" for p in numbers])
        country_display, _ = get_country_info(numbers[0])
        
        header_text = f"❓ Service: 📘 Facebook\n{country_display}\n\n{num_text}\n\n⏳ Waiting for OTP..."
        reply_markup = create_multi_number_markup(numbers)
        await update.message.reply_text(header_text, reply_markup=reply_markup, parse_mode="Markdown")
        
        for p, oid in orders:
            asyncio.create_task(poll_for_otp(update.effective_chat.id, oid, p, context))

    elif text == "⚙️ Set Range":
        USER_STATES[user_id] = "WAITING_FOR_RANGE"
        await update.message.reply_text("🔴 Please send your target number range (e.g. 22896 or 23762):")

    elif text == "🟢 Live Traffic":
        await update.message.reply_text("⏳ Fetching live traffic directly from Voltx panel...")
        traffic_data = fetch_live_traffic_from_panel()
        
        traffic_lines = ["📊 **PANEL LIVE TRAFFIC & RANGES**\n"]
        
        if traffic_data:
            if isinstance(traffic_data, list):
                for item in traffic_data:
                    r_code = str(item.get("rid") or item.get("range") or "N/A")
                    country_display, _ = get_country_info(r_code)
                    traffic_lines.append(f"🌐 `{r_code}` | {country_display}")
            elif isinstance(traffic_data, dict):
                for r_code, info in traffic_data.items():
                    country_display, _ = get_country_info(str(r_code))
                    traffic_lines.append(f"🌐 `{r_code}` | {country_display}")
            else:
                traffic_lines.append(f"`{traffic_data}`")
        else:
            traffic_lines.append("⚠️ Could not fetch live list automatically right now. You can use any valid active range ID.")
        
        traffic_lines.append("\n⚡ Copy a range and use **⚙️ Set Range** to target it!")
        await update.message.reply_text("\n".join(traffic_lines), parse_mode="Markdown")

    elif text == "💳 Balance":
        balance_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Withdraw via Binance", callback_data="withdraw_binance")],
            [InlineKeyboardButton("🔴 Set Binance ID", callback_data="set_binance")],
            [InlineKeyboardButton("📣 OTP Group ↗️️", url=f"https://t.me/{YOUR_TELEGRAM_USERNAME}")]
        ])
        await update.message.reply_text("Current Balance: $0.091\nBinance Pay ID: Not Set\n\nMinimum withdraw is $0.2", reply_markup=balance_markup)

    elif text == "📣 OTP Group":
        await update.message.reply_text(f"📣 Join our OTP Group: t.me/{YOUR_TELEGRAM_USERNAME}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    # Handle direct copy button click
    if query.data.startswith("copy_"):
        copied_num = query.data.replace("copy_", "")
        await query.answer(f"✅ Number Copied: {copied_num}", show_alert=True)
        return

    await query.answer()

    if query.data == "change_number":
        user_id = query.from_user.id
        user_range = USER_RANGES.get(user_id, "22896")
        
        numbers = []
        orders = []

        for _ in range(3):
            p, oid = get_voltx_real_number(target_range=user_range)
            if p and p not in numbers:
                numbers.append(p)
                if oid:
                    orders.append((p, oid))
            await asyncio.sleep(0.3)

        if not numbers:
            await query.message.reply_text(f"❌ No real numbers available in panel for range `{user_range}` right now.")
            return

        num_text = "\n".join([f"📱 `{p}`" for p in numbers])
        country_display, _ = get_country_info(numbers[0])

        header_text = f"❓ Service: 📘 Facebook\n{country_display}\n\n{num_text}\n\n⏳ Waiting for OTP..."
        reply_markup = create_multi_number_markup(numbers)
        await query.edit_message_text(header_text, reply_markup=reply_markup, parse_mode="Markdown")

        for p, oid in orders:
            asyncio.create_task(poll_for_otp(query.message.chat_id, oid, p, context))

    elif query.data == "change_country":
        await query.answer("Country list will be updated soon!", show_alert=True)
        
    elif query.data == "withdraw_binance":
        await query.answer("Minimum withdraw is $0.2", show_alert=True)
        
    elif query.data == "set_binance":
        await query.message.reply_text("Please send your Binance Pay ID:")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading

    class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running!")

    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    app.run_polling()
