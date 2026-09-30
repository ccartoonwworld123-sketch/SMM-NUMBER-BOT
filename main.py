import os
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, CopyTextButton
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
        return "Cameroon", "CM", "🇨🇲"
    elif clean_num.startswith("225"):
        return "Ivory Coast", "CI", "🇨🇮"
    elif clean_num.startswith("228"):
        return "Togo", "TG", "🇹🇬"
    elif clean_num.startswith("229"):
        return "Benin", "BJ", "🇧🇯"
    elif clean_num.startswith("255"):
        return "Tanzania", "TZ", "🇹🇿"
    elif clean_num.startswith("266"):
        return "Lesotho", "LS", "🇱🇸"
    elif clean_num.startswith("380"):
        return "Ukraine", "UA", "🇺🇦"
    elif clean_num.startswith("224"):
        return "Guinea", "GN", "🇬🇳"
    elif clean_num.startswith("996"):
        return "Kyrgyzstan", "KG", "🇰🇬"
    elif clean_num.startswith("43"):
        return "Austria", "AT", "🇦🇹"
    else:
        return "Togo", "TG", "🇹🇬"

def get_voltx_real_number(target_range="22896"):
    headers = {
        "mauthapi": VOLTX_API_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    clean_rid = str(target_range).upper().replace("XXX", "").replace("X", "").strip()
    payload = {"rid": clean_rid}
    
    try:
        res = requests.post(f"{BASE_API_URL}/getnum", headers=headers, json=payload, timeout=3)
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
    range_counts = {}
    total_hits = 0
    
    try:
        res = requests.get(f"{BASE_API_URL}/console", headers=headers, timeout=3)
        if res.status_code == 200:
            res_data = res.json()
            if res_data.get("meta", {}).get("code") == 200:
                hits = res_data.get("data", {}).get("hits", [])
                total_hits = len(hits)
                for hit in hits:
                    r = hit.get("range")
                    sid = hit.get("sid", "FACEBOOK")
                    if sid.upper() == "FB":
                        sid = "FACEBOOK"
                    if r:
                        clean_r = str(r).strip()
                        if clean_r in range_counts:
                            range_counts[clean_r]["count"] += 1
                        else:
                            range_counts[clean_r] = {"sid": sid.upper(), "count": 1}
    except Exception as e:
        print(f"Console API Error: {e}")

    if not range_counts:
        try:
            res = requests.get(f"{BASE_API_URL}/liveaccess", headers=headers, timeout=3)
            if res.status_code == 200:
                res_data = res.json()
                if res_data.get("meta", {}).get("code") == 200:
                    services = res_data.get("data", {}).get("services", [])
                    for s in services:
                        sid = s.get("id", "FACEBOOK")
                        if sid.upper() == "FB":
                            sid = "FACEBOOK"
                        for r in s.get("ranges", []):
                            clean_r = str(r).strip()
                            if clean_r in range_counts:
                                range_counts[clean_r]["count"] += 1
                            else:
                                range_counts[clean_r] = {"sid": sid.upper(), "count": 1}
                    total_hits = sum(item["count"] for item in range_counts.values())
        except Exception as e:
            print(f"Liveaccess API Error: {e}")

    sorted_ranges = sorted(range_counts.items(), key=lambda x: x[1]["count"], reverse=True)
    return sorted_ranges, total_hits

def check_voltx_otp(target_phone, order_id):
    headers = {
        "mauthapi": VOLTX_API_KEY,
        "Accept": "application/json"
    }
    
    clean_target = str(target_phone).replace("+", "").strip()
    
    try:
        res = requests.get(f"{BASE_API_URL}/console", headers=headers, timeout=2)
        if res.status_code == 200:
            res_data = res.json()
            if res_data.get("meta", {}).get("code") == 200:
                hits = res_data.get("data", {}).get("hits", [])
                for hit in hits:
                    num = str(hit.get("number", "")).replace("+", "").strip()
                    msg = str(hit.get("message", ""))
                    if clean_target in num or clean_target in msg:
                        import re
                        match = re.search(r'\b\d{4,6}\b', msg)
                        if match:
                            return match.group(0)
                        elif msg:
                            return msg
    except Exception:
        pass

    try:
        res = requests.get(f"{BASE_API_URL}/success-otp", headers=headers, timeout=2)
        if res.status_code == 200:
            res_data = res.json()
            if res_data.get("meta", {}).get("code") == 200:
                otps = res_data.get("data", {}).get("otps", [])
                for item in otps:
                    num = str(item.get("number", "")).replace("+", "").strip()
                    oid = str(item.get("otp_id", ""))
                    msg = str(item.get("message", ""))
                    
                    if clean_target in num or (order_id and order_id in oid) or clean_target in msg:
                        import re
                        match = re.search(r'\b\d{4,6}\b', msg)
                        if match:
                            return match.group(0)
                        elif msg:
                            return msg
    except Exception:
        pass
            
    return None

def create_number_markup(numbers_list):
    keyboard = []
    for num in numbers_list:
        _, _, flag = get_country_info(num)
        button_text = f"{flag} {num}"
        keyboard.append([
            InlineKeyboardButton(
                text=button_text,
                copy_text=CopyTextButton(text=num)
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton("🔔 OTP GROUP", url=f"https://t.me/{YOUR_TELEGRAM_USERNAME}"),
        InlineKeyboardButton("🔄 Change", callback_data="change_number")
    ])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_home")])
    return InlineKeyboardMarkup(keyboard)

async def poll_for_otp(chat_id, order_id, phone, context):
    # প্রতি ১ সেকেন্ড পরপর চেক করবে যাতে কোড আসার সাথে সাথেই নোটিফিকেশন চলে আসে
    for _ in range(120): 
        await asyncio.sleep(1)
        status = check_voltx_otp(phone, order_id)
        if status:
            otp_message = f"🚨 **NEW OTP RECEIVED!** 🚨\n\n📱 **Number:** `{phone}`\n🔑 **OTP Code:** `{status}`"
            try:
                await context.bot.send_message(
                    chat_id=chat_id, 
                    text=otp_message, 
                    parse_mode="Markdown",
                    disable_notification=False
                )
            except Exception as e:
                print(f"Notification Error: {e}")
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
        user_range = USER_RANGES.get(user_id, "22896")
        
        numbers = []
        orders = []

        for _ in range(2):
            p, oid = get_voltx_real_number(target_range=user_range)
            if p and p not in numbers:
                numbers.append(p)
                if oid:
                    orders.append((p, oid))

        if not numbers:
            await update.message.reply_text(f"❌ **No Real Number Available!**\n\nPanel has no stock for range `{user_range}`. Check **🟢 Live Traffic**.", parse_mode="Markdown")
            return

        country_name, _, flag = get_country_info(numbers[0])
        header_text = f"✅ **Number:** {flag} {country_name}"
        
        reply_markup = create_number_markup(numbers)
        await update.message.reply_text(header_text, reply_markup=reply_markup, parse_mode="Markdown")
        
        for p, oid in orders:
            asyncio.create_task(poll_for_otp(update.effective_chat.id, oid, p, context))

    elif text == "⚙️ Set Range":
        USER_STATES[user_id] = "WAITING_FOR_RANGE"
        await update.message.reply_text("🔴 Please send your target number range (e.g. 22896):")

    elif text == "🟢 Live Traffic":
        sorted_ranges, total_hits = fetch_live_traffic_from_panel()
        
        traffic_lines = [
            "📊 **Live Traffic**\n",
            f"📋 **Total OTP:** {total_hits}",
            f"⏱ **Record:** Last 15 Minutes"
        ]
        
        if sorted_ranges:
            top_r, top_info = sorted_ranges[0]
            _, _, top_flag = get_country_info(top_r)
            traffic_lines.append(f"👑 **Top Range:** {top_flag} `{top_r}` - {top_info['sid']}")
            traffic_lines.append("\n📥 **Range List**")
            
            for r, info in sorted_ranges:
                _, _, flag = get_country_info(r)
                traffic_lines.append(f"• {flag} `{r}` - {info['sid']} - {info['count']}")
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
    await query.answer()

    if query.data == "change_number":
        user_id = query.from_user.id
        user_range = USER_RANGES.get(user_id, "22896")
        
        numbers = []
        orders = []

        for _ in range(2):
            p, oid = get_voltx_real_number(target_range=user_range)
            if p and p not in numbers:
                numbers.append(p)
                if oid:
                    orders.append((p, oid))

        if not numbers:
            return

        country_name, _, flag = get_country_info(numbers[0])
        header_text = f"✅ **Number:** {flag} {country_name}"
        
        reply_markup = create_number_markup(numbers)
        try:
            await query.edit_message_text(header_text, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception:
            pass

        for p, oid in orders:
            asyncio.create_task(poll_for_otp(query.message.chat_id, oid, p, context))

    elif query.data == "back_home":
        try:
            await query.message.delete()
        except Exception:
            pass
        await start(update, context)

    elif query.data == "withdraw_binance":
        pass
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
        do_GET = lambda self, *a: (self.send_response(200), self.end_headers(), self.wfile.write(b"Bot is running!"))

    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    app.run_polling()
