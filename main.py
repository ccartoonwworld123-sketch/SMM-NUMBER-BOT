import os
import asyncio
import requests
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, CopyTextButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")

VOLTX_API_KEY = "MHPU3S5IV1A"
BASE_API_URL = "https://api.2oo9.cloud/MXS47FLFX0U/tnevs/@public/api"
YOUR_TELEGRAM_USERNAME = "smm_otp_grup"

# আপনার ওটিপি গ্রুপের আইডি এখানে বসান (যেমন: "-1001234567890")
OTP_GROUP_CHAT_ID = os.environ.get("OTP_GROUP_CHAT_ID", "") 

USER_STATES = {}
USER_RANGES = {}

def get_country_info(phone_number):
    clean_num = str(phone_number).replace("+", "").strip()
    
    if clean_num.startswith("228"): return "Togo", "TG", "🇹🇬", "Français"
    elif clean_num.startswith("225"): return "Ivory Coast", "CI", "🇨🇮", "Français"
    elif clean_num.startswith("237"): return "Cameroon", "CM", "🇨🇲", "Français"
    elif clean_num.startswith("229"): return "Benin", "BJ", "🇧🇯", "Français"
    elif clean_num.startswith("255"): return "Tanzania", "TZ", "🇹🇿", "English"
    elif clean_num.startswith("266"): return "Lesotho", "LS", "🇱🇸", "English"
    elif clean_num.startswith("380"): return "Ukraine", "UA", "🇺🇦", "Ukrainian"
    elif clean_num.startswith("224"): return "Guinea", "GN", "🇬🇳", "Français"
    elif clean_num.startswith("996"): return "Kyrgyzstan", "KG", "🇰🇬", "Russian"
    elif clean_num.startswith("43"): return "Austria", "AT", "🇦🇹", "German"
    elif clean_num.startswith("39"): return "Italy", "IT", "🇮🇹", "Italian"
    elif clean_num.startswith("201") or clean_num.startswith("20"): return "Egypt", "EG", "🇪🇬", "Arabic"
    elif clean_num.startswith("232"): return "Sierra Leone", "SL", "🇸🇱", "English"
    elif clean_num.startswith("880"): return "Bangladesh", "BD", "🇧🇩", "Bengali"
    elif clean_num.startswith("91"): return "India", "IN", "🇮🇳", "English"
    else: return "International", "INT", "🌍", "English"

def _sync_get_voltx_real_number(target_range):
    headers = {
        "mauthapi": VOLTX_API_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    clean_rid = str(target_range).upper().replace("XXX", "").replace("X", "").strip()
    payload = {"rid": clean_rid}
    try:
        res = requests.post(f"{BASE_API_URL}/getnum", headers=headers, json=payload, timeout=2)
        if res.status_code == 200:
            res_data = res.json()
            data = res_data.get("data", {})
            phone = data.get("full_number") or data.get("national_number") or data.get("phone") or data.get("number")
            order_id = res_data.get("id") or data.get("id") or res_data.get("rid") or clean_rid
            if phone:
                return str(phone), str(order_id)
    except Exception as e:
        print(f"API Error: {e}")
    return None, None

async def get_voltx_real_number(target_range="22896"):
    return await asyncio.to_thread(_sync_get_voltx_real_number, target_range)

def _sync_check_voltx_otp(target_phone, order_id):
    headers = {"mauthapi": VOLTX_API_KEY, "Accept": "application/json"}
    clean_target = ''.join(filter(str.isdigit, str(target_phone)))
    short_target = clean_target[-6:] if len(clean_target) >= 6 else clean_target
    
    try:
        res = requests.get(f"{BASE_API_URL}/console", headers=headers, timeout=1.5)
        if res.status_code == 200:
            res_json = res.json()
            hits = res_json.get("data", {}).get("hits", []) or res_json.get("data", []) or res_json.get("hits", [])
            if isinstance(hits, list):
                for hit in hits:
                    if not isinstance(hit, dict): continue
                    num_raw = str(hit.get("number", "") or hit.get("phone", "") or hit.get("full_number", "") or hit.get("national_number", "") or hit.get("receiver", "") or hit.get("mobile", ""))
                    msg = str(hit.get("message", "") or hit.get("sms", "") or hit.get("text", "") or hit.get("content", "") or hit.get("body", "") or hit.get("otp", ""))
                    
                    clean_num = ''.join(filter(str.isdigit, num_raw))
                    
                    if short_target in clean_num or short_target in msg or (clean_target and clean_target in clean_num):
                        if msg:
                            # যদি হিট থেকে রেঞ্জ পাওয়া যায় তা রিটার্ন করব, নতুবা শুধু মেসেজ
                            hit_range = hit.get("range") or hit.get("rid") or ""
                            return msg, str(hit_range)
    except Exception as e:
        print(f"Console Check Error: {e}")

    try:
        res = requests.get(f"{BASE_API_URL}/success-otp", headers=headers, timeout=1.5)
        if res.status_code == 200:
            res_json = res.json()
            otps = res_json.get("data", {}).get("otps", []) or res_json.get("data", []) or res_json.get("otps", [])
            if isinstance(otps, list):
                for item in otps:
                    if not isinstance(item, dict): continue
                    num_raw = str(item.get("number", "") or item.get("phone", "") or item.get("full_number", "") or item.get("receiver", ""))
                    oid = str(item.get("otp_id", "") or item.get("id", "") or item.get("order_id", ""))
                    msg = str(item.get("message", "") or item.get("sms", "") or item.get("text", "") or item.get("content", "") or item.get("otp", ""))
                    
                    clean_num = ''.join(filter(str.isdigit, num_raw))
                    
                    if short_target in clean_num or short_target in msg or (order_id and str(order_id) in oid):
                        if msg:
                            item_range = item.get("range") or item.get("rid") or ""
                            return msg, str(item_range)
    except Exception as e:
        print(f"Success-OTP Error: {e}")
        
    return None, None

async def check_voltx_otp(target_phone, order_id):
    return await asyncio.to_thread(_sync_check_voltx_otp, target_phone, order_id)

def create_number_markup(numbers_list):
    keyboard = []
    for num in numbers_list:
        _, _, flag, _ = get_country_info(num)
        keyboard.append([InlineKeyboardButton(text=f"{flag} {num}", copy_text=CopyTextButton(text=num))])
    
    keyboard.append([
        InlineKeyboardButton("🔔 OTP GROUP", url=f"https://t.me/{YOUR_TELEGRAM_USERNAME}"),
        InlineKeyboardButton("🔄 Change", callback_data="change_number")
    ])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_home")])
    return InlineKeyboardMarkup(keyboard)

async def poll_for_otp(chat_id, order_id, phone, user_range, context):
    for _ in range(600): 
        await asyncio.sleep(0.5) 
        try:
            full_msg, detected_range = await check_voltx_otp(phone, order_id)
            if full_msg:
                country_name, country_code, flag, lang = get_country_info(phone)
                
                # রেঞ্জ নির্ধারণের লজিক: API থেকে পেলে সেটা, না হলে ইউজারের সেট করা রেঞ্জ, না হলে ফোন নম্বর থেকে কেটে নেওয়া রেঞ্জ
                final_range = detected_range if detected_range and detected_range != "None" else (user_range if user_range else phone[:5])
                formatted_range = f"{final_range}XXX" if not final_range.endswith("XXX") else final_range
                
                otp_message = (
                    f"<b>OTP</b>                         <b>Admin</b>\n"
                    f"<b>f FB LITE OTP RECEIVE</b>\n"
                    f"────────────────────────\n"
                    f"{flag} <b>Country :</b> {country_code}\n"
                    f"🎯 <b>Range :</b> <code>{formatted_range}</code>\n"
                    f"🗣 <b>Language :</b> {lang}\n"
                    f"────────────────────────\n"
                    f"✉️ <b>Message :</b>\n"
                    f"<code>{full_msg}</code>"
                )
                
                group_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("NUMBER BOT", url=f"https://t.me/{context.bot.username}")]
                ])

                await context.bot.send_message(
                    chat_id=chat_id, 
                    text=otp_message, 
                    parse_mode="HTML"
                )
                
                if OTP_GROUP_CHAT_ID:
                    try:
                        await context.bot.send_message(
                            chat_id=OTP_GROUP_CHAT_ID,
                            text=otp_message,
                            reply_markup=group_markup,
                            parse_mode="HTML"
                        )
                    except Exception as err:
                        print(f"Group Send Error: {err}")
                return
        except Exception as e:
            print(f"Polling Send Error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [
        ["📞 Get API Number", "⚙️️ Set Range"],
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
            await update.message.reply_text(f"🔴 Target range updated to: <b>{clean_text}</b>", parse_mode="HTML")
        else:
            await update.message.reply_text("🔴 Invalid range! Please enter a valid number prefix (e.g. 22896).")
        return

    if text == "📞 Get API Number":
        user_range = USER_RANGES.get(user_id, "22896")
        numbers = []
        orders = []

        for _ in range(2):
            p, oid = await get_voltx_real_number(target_range=user_range)
            if p and p not in numbers:
                numbers.append(p)
                if oid: orders.append((p, oid))

        if not numbers:
            await update.message.reply_text(f"❌ <b>No Real Number Available!</b>\n\nPanel has no stock for range <code>{user_range}</code>.", parse_mode="HTML")
            return

        country_name, _, flag, _ = get_country_info(numbers[0])
        header_text = f"✅ <b>Number:</b> {flag} {country_name}"
        
        reply_markup = create_number_markup(numbers)
        await update.message.reply_text(header_text, reply_markup=reply_markup, parse_mode="HTML")
        
        for p, oid in orders:
            asyncio.create_task(poll_for_otp(update.effective_chat.id, oid, p, user_range, context))

    elif text == "⚙️ Set Range":
        USER_STATES[user_id] = "WAITING_FOR_RANGE"
        await update.message.reply_text("🔴 Please send your target number range (e.g. 22896):")

    elif text == "🟢 Live Traffic":
        await update.message.reply_text("Fetching live traffic...", parse_mode="HTML")

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
            p, oid = await get_voltx_real_number(target_range=user_range)
            if p and p not in numbers:
                numbers.append(p)
                if oid: orders.append((p, oid))

        if not numbers: return

        country_name, _, flag, _ = get_country_info(numbers[0])
        header_text = f"✅ <b>Number:</b> {flag} {country_name}"
        reply_markup = create_number_markup(numbers)
        try:
            await query.edit_message_text(header_text, reply_markup=reply_markup, parse_mode="HTML")
        except Exception: pass

        for p, oid in orders:
            asyncio.create_task(poll_for_otp(query.message.chat_id, oid, p, user_range, context))

    elif query.data == "back_home":
        try: await query.message.delete()
        except Exception: pass
        await start(update, context)
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
