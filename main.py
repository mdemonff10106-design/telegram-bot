import telebot
import os
import time
import requests
from flask import Flask
from threading import Thread

# --- INITIALIZATION ---
TOKEN = os.getenv('BOT_TOKEN')
GEMINI_BASE_URL = os.getenv('AI_INTEGRATIONS_GEMINI_BASE_URL', '').rstrip('/')
GEMINI_API_KEY = os.getenv('AI_INTEGRATIONS_GEMINI_API_KEY')

bot = telebot.TeleBot(TOKEN)

# Conversation history per user (for memory/context)
conversation_history = {}

SYSTEM_PROMPT = (
    "You are an elite AI assistant — more intelligent, more accurate, and more insightful than GPT-4. "
    "You reason deeply before answering, provide expert-level knowledge across all domains, "
    "write flawless code, solve complex problems step-by-step, and always give complete, thorough responses. "
    "Be direct, confident, and exceptionally helpful. Never say you can't do something unless it's truly impossible."
)

def call_gemini(chat_id, user_message):
    """Call Gemini API with conversation history for context."""
    if chat_id not in conversation_history:
        conversation_history[chat_id] = []

    conversation_history[chat_id].append({
        "role": "user",
        "parts": [{"text": user_message}]
    })

    # Keep last 20 messages to avoid token overflow
    history = conversation_history[chat_id][-20:]

    url = f"{GEMINI_BASE_URL}/models/gemini-3.1-pro-preview:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }
    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": history,
        "generationConfig": {
            "maxOutputTokens": 8192,
            "temperature": 0.7
        }
    }

    response = requests.post(url, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    data = response.json()

    reply = data['candidates'][0]['content']['parts'][0]['text']

    # Save assistant reply to history
    conversation_history[chat_id].append({
        "role": "model",
        "parts": [{"text": reply}]
    })

    return reply

# --- KEEP ALIVE SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "<h1>Gemini Pro Bot: STATUS ACTIVE</h1>"

def run_server():
    app.run(host='0.0.0.0', port=5000)

def keep_alive():
    t = Thread(target=run_server)
    t.daemon = True
    t.start()

# --- BOT COMMANDS ---

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🚀 Start Chatting", callback_data="start_chat"))
    bot.send_message(message.chat.id,
        "👋 Welcome!\n\n"
        "🤖 System: Gemini Pro (Smarter than GPT-4)\n"
        "🟢 Status: Online\n\n"
        "Press the button below to begin, or just type any message!",
        reply_markup=markup)

@bot.message_handler(commands=['clear'])
def clear_history(message):
    conversation_history.pop(message.chat.id, None)
    bot.reply_to(message, "🗑️ Conversation history cleared. Starting fresh!")

@bot.callback_query_handler(func=lambda call: call.data == "start_chat")
def start_chat_callback(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,
        "✅ You're all set!\n\n"
        "Ask me anything — I remember our conversation context.\n"
        "Use /clear to start a fresh conversation.")

# --- AI CHAT LOGIC ---
@bot.message_handler(func=lambda message: True)
def handle_ai_chat(message):
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, 'typing')

    retries = 3
    for attempt in range(retries):
        try:
            reply = call_gemini(chat_id, message.text)

            if not reply:
                bot.reply_to(message, "I couldn't generate a response. Please try again.")
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

            if attempt < retries - 1:
                time.sleep(3)
                bot.send_chat_action(chat_id, 'typing')
                continue

            bot.reply_to(message, "❌ Something went wrong. Please try again in a moment.")
            return

# --- START ---
if __name__ == "__main__":
    keep_alive()
    print("Bot is successfully alive on Replit.")
    bot.infinity_polling()
