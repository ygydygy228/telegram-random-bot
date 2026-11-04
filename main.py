import os
import random
import sqlite3
import logging
from html import escape

import requests
from flask import Flask, request, abort

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]
APP_URL = os.environ.get("APP_URL", "").rstrip("/")
DB_PATH = os.environ.get("DB_PATH", "members.db")
API = f"https://api.telegram.org/bot{BOT_TOKEN}"


def db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS members (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                username TEXT,
                PRIMARY KEY (chat_id, user_id)
            )
        """)


def telegram(method, payload=None):
    response = requests.post(f"{API}/{method}", json=payload or {}, timeout=20)
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("description", "Telegram API error"))
    return data.get("result")


def send(chat_id, text, parse_mode="HTML"):
    return telegram("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    })


def user_name(user):
    name = " ".join(x for x in [user.get("first_name"), user.get("last_name")] if x)
    return name or user.get("username") or "Участник"


def handle_message(message):
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    if not chat_id:
        return

    user = message.get("from", {})
    if user.get("is_bot"):
        return

    text = (message.get("text") or "").strip()
    command = text.split()[0].split("@")[0].lower() if text.startswith("/") else ""
    name = user_name(user)
    user_id = user.get("id")

    if command in ("/start", "/help"):
        send(chat_id,
             "🎲 <b>Бот случайного выбора</b>\n\n"
             "Нажми /join, чтобы попасть в список участников.\n"
             "/leave — выйти из списка\n"
             "/random — выбрать случайного участника\n"
             "/list — показать список участников\n"
             "/help — помощь")
    elif command == "/join":
        with db() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO members(chat_id, user_id, name, username) VALUES (?, ?, ?, ?)",
                (chat_id, user_id, name, user.get("username"))
            )
        send(chat_id, f"✅ {escape(name)}, ты добавлен(а) в список!")
    elif command == "/leave":
        with db() as conn:
            conn.execute("DELETE FROM members WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        send(chat_id, f"👋 {escape(name)}, ты удалён(а) из списка.")
    elif command == "/list":
        with db() as conn:
            members = conn.execute(
                "SELECT name FROM members WHERE chat_id = ? ORDER BY name COLLATE NOCASE",
                (chat_id,)
            ).fetchall()
        if not members:
            send(chat_id, "Список пока пуст. Напиши /join, чтобы добавиться.")
        else:
            lines = [f"• {escape(row['name'])}" for row in members]
            send(chat_id, f"👥 <b>Участники ({len(members)}):</b>\n" + "\n".join(lines))
    elif command == "/random":
        with db() as conn:
            members = conn.execute(
                "SELECT user_id, name FROM members WHERE chat_id = ?",
                (chat_id,)
            ).fetchall()
        if not members:
            send(chat_id, "Пока некого выбирать. Сначала участники должны написать /join.")
        else:
            chosen = random.choice(members)
            mention = f'<a href="tg://user?id={chosen["user_id"]}">{escape(chosen["name"])}</a>'
            send(chat_id, f"🎯 Случайный выбор: {mention}!")


@app.get("/")
def health():
    return "Bot is running", 200


@app.post("/webhook/" + WEBHOOK_SECRET)
def webhook():
    update = request.get_json(silent=True) or {}
    message = update.get("message") or update.get("edited_message")
    if message:
        try:
            handle_message(message)
        except Exception:
            logging.exception("Failed to process Telegram update")
    return "OK", 200


if __name__ == "__main__":
    init_db()
    if APP_URL:
        telegram("setWebhook", {
            "url": f"{APP_URL}/webhook/{WEBHOOK_SECRET}",
            "secret_token": WEBHOOK_SECRET
        })
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
else:
    init_db()
