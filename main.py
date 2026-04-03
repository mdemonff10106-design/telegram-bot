import telebot
import os
import time
from google import genai
from google.genai import types
from flask import Flask
from threading import Thread

# --- INITIALIZATION ---
TOKEN = os.getenv('BOT_TOKEN')
GEMINI_BASE_URL = os.getenv('AI_INTEGRATIONS_GEMINI_BASE_URL')
GEMINI_API_KEY = os.getenv('AI_INTEGRATIONS_GEMINI_API_KEY')

bot = telebot.TeleBot(TOKEN)
client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(base_url=GEMINI_BASE_URL)
)

# --- KEEP ALIVE SYSTEM ---
app = Flask('')

@app.route('/')
def home():
    return "<h1>Gemini Bot: STATUS ACTIVE</h1>"

def run_server():
    app.run(host='0.0.0.0', port=5000)

def keep_alive():
    t = Thread(target=run_server)
    t.daemon = True
    t.start()

# --- BOT INTERFACE ---

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🚀 Start Chatting", callback_data="start_chat"))
    bot.send_message(message.chat.id,
        "👋 Welcome!\n\n"
        "🤖 System: Gemini 2.5 Flash\n"
        "🟢 Status: Online\n\n"
        "Press the button below to begin, or just type any message!",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "start_chat")
def start_chat_callback(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,
        "✅ You're all set! Ask me anything — I can write code, solve problems, answer questions, and more.")

# --- AI CHAT LOGIC ---
@bot.message_handler(func=lambda message: True)
def handle_ai_chat(message):
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, 'typing')

    retries = 3
    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=message.text
            )

            reply = response.text
            if not reply:
                bot.reply_to(message, "I couldn't generate a response. Please try asking again.")
                return

            # Handle long responses (Telegram limit is 4096)
            if len(reply) > 4000:
                for i in range(0, len(reply), 4000):
                    bot.send_message(chat_id, reply[i:i+4000])
            else:
                try:
                    bot.reply_to(message, reply, parse_mode="Markdown")
                except Exception:
                    bot.reply_to(message, reply)
            return

        except Exception as e:
            error_str = str(e)
            print(f"Attempt {attempt + 1} error: {error_str}")

            if '429' in error_str and attempt < retries - 1:
                time.sleep(5)
                bot.send_chat_action(chat_id, 'typing')
                continue

            bot.reply_to(message, "❌ Something went wrong. Please try again in a moment.")
            return

# --- START ---
if __name__ == "__main__":
    keep_alive()
    print("Bot is successfully alive on Replit.")
    bot.infinity_polling()
