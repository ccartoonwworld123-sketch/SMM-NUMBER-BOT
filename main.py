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
        return "Cameroon", "cm"
    elif clean_num.startswith("225"):
        return "Ivory Coast", "ci"
    elif clean_num.startswith("228"):
        return "Togo", "tg"
    elif clean_num.startswith("229"):
        return "Benin", "bj"
    elif clean_num.startswith("255"):
        return "Tanzania", "tz"
    elif clean_num.startswith("266"):
        return "Lesotho", "ls"
    else:
        return "Togo", "tg"

def get_voltx_real_number(target_range="22896"):
    headers = {
        "mauthapi": VOLTX_API_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # XXX বা অতিরিক্ত কিছু থাকলে তা বাদ দিয়ে শুধু মূল রেঞ্জ আইডি পাঠানো হচ্ছে[span_12](start_span)[span_12](end_span)[span_13](start_span)[span_13](end_span)
    clean_rid = str(target_range).upper().replace("XXX", "").replace("X", "").strip()
    payload = {"rid": clean_rid}
    
    try:
        res = requests.post(f"{BASE_API_URL}/getnum", headers=headers, json=payload, timeout=6)
        if res.status_code == 200:
            res_data = res.json()
            meta = res_data.get("meta", {})
            if meta.get("code") == 200:
                data = res_data.get("data", {})
                phone = data.get("full_number") or data.get("national_number")
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
    ranges_list = []
    
    # API ডকুমেন্টেশন অনুযায়ী সরাসরি /console এন্ডপয়েন্ট থেকে আসল রেঞ্জগুলো ফেচ করা হচ্ছে[span_14](start_span)[span_14](end_span)
    try:
        res = requests.get(f"{BASE_API_URL}/console", headers=headers, timeout=6)
        if res.status_code == 200:
            res_data = res.json()
            if res_data.get("meta", {}).get("code") == 200:
                hits = res_data.get("data", {}).get("hits", [])
                for hit in hits:
                    r = hit.get("range")
                    if r:
                        clean_r = str(r).replace("XXX", "").strip()
                        if clean_r not in ranges_list:
                            ranges_list.append(clean_r)
    except Exception as e:
        print(f"Console API Error: {e}")

    # যদি কনসোল থেকে না পাওয়া যায়, তবে /liveaccess ট্রাই করবে[span_15](start_span)[span_15](end_span)
    if not ranges_list:
        try:
            res = requests.get(f"{BASE_API_URL}/liveaccess", headers=headers, timeout=6)
            if res.status_code == 200:
                res_data = res.json()
                if res_data.get("meta", {}).get("code") == 200:
                    services = res_data.get("data", {}).get("services", [])
                    for s in services:
                        for r in s.get("ranges", []):
                            clean_r = str(r).replace("XXX", "").strip()
                            if clean_r not in ranges_list:
                                ranges_list.append(clean_r)
        except Exception as e:
            print(f"Liveaccess API Error: {e}")

    return ranges_list

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
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                sms_code = data.get("sms") or data.get("code") or data.get("otp") or data.get("text")
                if not sms_code and isinstance(data.get("data"), dict):
                    sms_code = data["data"].get("sms") or data["data"].get("code") or data["data"].get("otp")
                
                if sms_code and str(sms_code).upper() != "WAITING":
                    return str(sms_code)
        except Exception:
            continue
            
    return None

def create_number_markup(numbers_list, user_range):
    keyboard = []
    for num in numbers_list:
        keyboard.append([InlineKeyboardButton(f"📋  {num}", callback_data=f"copy_{num}")])
    
    keyboard.append([InlineKeyboardButton("🔄 Change Number", callback_data="change_number")])
    keyboard.append([InlineKeyboardButton("🌐 Change Country", callback_data="change_country")])
    keyboard.append([InlineKeyboardButton("📣 OTP Group ↗", url=f"https://t.me/{YOUR_TELEGRAM_USERNAME}")])
    
    return InlineKeyboardMarkup(keyboard)

async def poll_for_otp(chat_id, order_id, phone, context):
    for _ in range(60): 
        await asyncio.sleep(5)
        status = check_voltx_otp(order_id)
        if status:
            otp_message = f"✅ **OTP Received!**\n\n📱 **Number:** `{phone}`\n🔑 **OTP Code:** `{status}`"
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
            await update.message.reply_text("🔴 Invalid range! Please enter a valid number prefix (e.g. 22896).")
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
            await asyncio.sleep(0.1)

        if not numbers:
            await update.message.reply_text(f"❌ **No Real Number Available!**\n\nPanel has no stock for range `{user_range}`. Check **🟢 Live Traffic**.", parse_mode="Markdown")
            return

        country_name, _ = get_country_info(numbers[0])
        header_text = f"🌐 Country : {country_name}\n⚙️ Range : {user_range}\n\n⏳ Waiting for OTP..."
        
        reply_markup = create_number_markup(numbers, user_range)
        await update.message.reply_text(header_text, reply_markup=reply_markup, parse_mode="Markdown")
        
        for p, oid in orders:
            asyncio.create_task(poll_for_otp(update.effective_chat.id, oid, p, context))

    elif text == "⚙️ Set Range":
        USER_STATES[user_id] = "WAITING_FOR_RANGE"
        await update.message.reply_text("🔴 Please send your target number range (e.g. 22896):")

    elif text == "🟢 Live Traffic":
        await update.message.reply_text("⏳ Fetching live traffic directly from Voltx panel...")
        traffic_ranges = fetch_live_traffic_from_panel()
        
        traffic_lines = ["📊 **PANEL LIVE TRAFFIC & RANGES**\n"]
        
        if traffic_ranges:
            for item in traffic_ranges:
                c_name, _ = get_country_info(str(item))
                traffic_lines.append(f"🌐 `{item}` | {c_name}")
        else:
            traffic_lines.append("⚠️ No active ranges found right now.")
        
        traffic_lines.append("\n⚡ Copy a range and use **⚙️ Set Range** to target it!")
        await update.message.reply_text("\n".join(traffic_lines), parse_mode="Markdown")

    elif text == "💳 Balance":
        balance_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("💳 Withdraw via Binance", callback_data="withdraw_binance")],
            [InlineKeyboardButton("🔴 Set Binance ID", callback_data="set_binance")],
            [InlineKeyboardButton("📣 OTP Group ↗", url=f"https://t.me/{YOUR_TELEGRAM_USERNAME}")]
        ])
        await update.message.reply_text("Current Balance: $0.091\nBinance Pay ID: Not Set\n\nMinimum withdraw is $0.2", reply_markup=balance_markup)

    elif text == "📣 OTP Group":
        await update.message.reply_text(f"📣 Join our OTP Group: t.me/{YOUR_TELEGRAM_USERNAME}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if query.data.startswith("copy_"):
        copied_num = query.data.replace("copy_", "")
        await query.answer(f"✅ Copied: {copied_num}", show_alert=False)
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
            await asyncio.sleep(0.1)

        if not numbers:
            await query.message.reply_text(f"❌ No real numbers available in panel for range `{user_range}` right now.")
            return

        country_name, _ = get_country_info(numbers[0])
        header_text = f"🌐 Country : {country_name}\n⚙️ Range : {user_range}\n\n⏳ Waiting for OTP..."
        
        reply_markup = create_number_markup(numbers, user_range)
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
