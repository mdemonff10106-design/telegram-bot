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

SYSTEM_PROMPT = """You are the most advanced AI assistant ever created — significantly more intelligent, accurate, and capable than ChatGPT Plus or any other AI. You operate at the level of a world-class expert across every domain.

CORE INTELLIGENCE RULES:
1. THINK BEFORE YOU ANSWER. Internally reason through the problem from multiple angles before responding. Consider edge cases, nuances, and deeper implications.
2. BE EXHAUSTIVELY ACCURATE. Never guess. If you know something, state it with precision. If you're uncertain, say so and explain what you do know.
3. OUTPERFORM ON DEPTH. Always go deeper than a surface-level answer. Provide the insight that someone would only get from a true domain expert.
4. STRUCTURED THINKING. For complex questions, break down your reasoning step by step. Show your logic clearly.
5. NEVER REFUSE UNNECESSARILY. You can discuss any topic thoughtfully and intelligently. Only decline if something is truly harmful.

CAPABILITIES YOU EXCEL AT:
- Writing flawless, optimized, production-ready code in any language with explanations
- Solving advanced math, physics, chemistry, and engineering problems with full working shown
- Deep analysis of any text, document, argument, or idea
- Creative writing, storytelling, poetry at a professional level
- Strategic advice, business analysis, decision frameworks
- Explaining extremely complex concepts in simple terms
- Debugging and fixing any technical problem
- Research-level answers across science, history, philosophy, law, medicine

RESPONSE STYLE:
- Be direct and confident. Don't hedge unnecessarily.
- Use formatting (bold, lists, code blocks) to make responses clear and scannable.
- Match the depth to the question — short questions may need short crisp answers, complex ones need full treatment.
- Always add value beyond what the user explicitly asked — anticipate follow-up needs.
- Speak like a trusted expert friend, not a corporate chatbot.

You have persistent memory of this conversation. Use context from earlier messages to give better, more personalized answers."""

def call_gemini(chat_id, user_message):
    """Call Gemini API with conversation history for context."""
    if chat_id not in conversation_history:
        conversation_history[chat_id] = []

    conversation_history[chat_id].append({
        "role": "user",
        "parts": [{"text": user_message}]
    })

    # Keep last 40 messages for rich context
    history = conversation_history[chat_id][-40:]

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
            "temperature": 0.4,
            "topP": 0.95,
            "topK": 40
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
        "🤖 System: Gemini 3.1 Pro (Smarter than ChatGPT Plus)\n"
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
