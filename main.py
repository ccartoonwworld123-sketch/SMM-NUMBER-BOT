import os
import time
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
# CONFIG CHECK
# =========================================================

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN environment variable is missing."
    )

if not VOLTX_API_KEY:
    raise RuntimeError(
        "VOLTX_API_KEY environment variable is missing."
    )


# =========================================================
# VOLTX API HEADERS
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
# API REQUEST
# =========================================================

def api_request(method, endpoint, **kwargs):

    url = f"{BASE_API_URL}/{endpoint.lstrip('/')}"

    try:

        response = requests.request(
            method=method,
            url=url,
            headers=API_HEADERS,
            timeout=20,
            **kwargs
        )

        print("--------------------------------")
        print("API REQUEST")
        print("METHOD:", method)
        print("URL:", url)
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text[:2000])
        print("--------------------------------")

        try:
            data = response.json()

        except Value
