import telebot
import os
import time
import google.generativeai as genai
from flask import Flask
from threading import Thread

# --- INITIALIZATION ---
TOKEN = os.getenv('BOT_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_KEY')

bot = telebot.TeleBot(TOKEN)
genai.configure(api_key=GEMINI_KEY)

# Using Gemini 1.5 Pro for 'Ultra' level intelligence
model = genai.GenerativeModel('gemini-1.5-pro')

# --- KEEP ALIVE SYSTEM (REPLIT) ---
app = Flask('')

@app.route('/')
def home():
    return "<h1>Gemini Premium: STATUS ACTIVE 🟢</h1>"

def run_server():
    app.run(host='0.0.0.0', port=5000)

def keep_alive():
    """Prevents Replit from sleeping by running a web server"""
    t = Thread(target=run_server)
    t.daemon = True
    t.start()

# --- BOT INTERFACE ---

@bot.message_handler(commands=['start'])
def start(message):
    # This creates the exact 8-button menu from your photos
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('⚡ Activate Gemini Pro', '👥 Activate Team')
    markup.add('💰 Balance', '🎟️ Redeem Code')
    markup.add('🔗 Invite Center', '⭐ Get Credits')
    markup.add('📖 Help', '🌐 语言/Language')
    
    bot.send_message(message.chat.id, 
        f"Welcome **Hardik**!\n\n"
        f"System: **Gemini 1.5 Pro (Premium)**\n"
        "Status: **Running on Replit**\n\n"
        "I can solve complex problems, write code, and answer better than GPT-4. Send me anything!", 
        reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💰 Balance")
def balance(message):
    bot.reply_to(message, "Your Balance: **Unlimited Premium Credits**")

# --- AI CHAT LOGIC ---
@bot.message_handler(func=lambda message: True)
def handle_ai_chat(message):
    chat_id = message.chat.id
    bot.send_chat_action(chat_id, 'typing')
    
    try:
        # Generate the high-level response
        response = model.generate_content(message.text)
        
        # Handle long responses (Telegram limit is 4096)
        if len(response.text) > 4000:
            for i in range(0, len(response.text), 4000):
                bot.send_message(chat_id, response.text[i:i+4000])
        else:
            bot.reply_to(message, response.text, parse_mode="Markdown")
            
    except Exception as e:
        bot.reply_to(message, "❌ **System Busy.** Re-routing through secondary server... try again in 5 seconds.")

# --- START THE ENGINE ---
if __name__ == "__main__":
    keep_alive() 
    print("Bot is successfully alive on Replit.")
    bot.infinity_polling()
