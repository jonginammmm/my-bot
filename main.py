import logging
import sqlite3
import time
import requests

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

# ================= CONFIG =================
BOT_TOKEN = "8623674613:AAFTRjJJDT9VKEaSiR1rF0xs1GY8LaGUWp0"
HF_TOKEN = "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"
REPLICATE_TOKEN = "r8_dm59oW3UreGLHdfUhsUCZJoHQLdt4Ha3Jwe4Z"
ADMIN_ID = 6394219796

# ================= INIT =================
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ================= DB =================
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    phone TEXT,
    created_at TEXT
)
""")
conn.commit()

# ================= SECURITY =================
last_msg = {}

def is_spam(user_id):
    now = time.time()
    if user_id in last_msg and now - last_msg[user_id] < 1:
        return True
    last_msg[user_id] = now
    return False

# ================= SAVE USER =================
def save_user(user_id, phone):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?)",
                   (user_id, phone, time.ctime()))
    conn.commit()

# ================= AI CHAT =================
def ai_chat(text):
    try:
        API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}

        res = requests.post(API_URL, headers=headers, json={"inputs": text})
        data = res.json()

        if isinstance(data, list):
            return data[0]["generated_text"]

        return "AI javob bera olmadi 😔"
    except:
        return "AI xatolik 😔"

# ================= IMAGE =================
def upscale_image(url):
    try:
        headers = {
            "Authorization": f"Token {REPLICATE_TOKEN}",
            "Content-Type": "application/json"
        }

        data = {
            "version": "nightmareai/real-esrgan",
            "input": {"image": url}
        }

        requests.post("https://api.replicate.com/v1/predictions",
                      headers=headers, json=data)

        return "🖼 Rasm processing boshlandi (demo)"
    except:
        return "Rasm xatolik 😔"

# ================= ISLAM =================
def islamic_answer(text):
    t = text.lower()
    if "namoz" in t:
        return "Namoz Islomning 5 ustunidan biridir."
    elif "roza" in t:
        return "Ro‘za sabr va taqvo maktabidir."
    return "Islomiy savol AI orqali ko‘rib chiqilmoqda..."

# ================= KEYBOARD =================
kb = ReplyKeyboardMarkup(resize_keyboard=True)
kb.add("🤖 AI Chat", "🖼 Rasm HD")
kb.add("☪️ Islomiy savol", "📊 Admin")

contact_kb = ReplyKeyboardMarkup(resize_keyboard=True)
contact_kb.add(KeyboardButton("📱 Raqam yuborish", request_contact=True))

# ================= START =================
@dp.message_handler(commands=['start'])
async def start(msg: types.Message):
    await msg.answer("📱 Raqamingizni yuboring:", reply_markup=contact_kb)

# ================= CONTACT =================
@dp.message_handler(content_types=['contact'])
async def contact(msg: types.Message):
    save_user(msg.from_user.id, msg.contact.phone_number)
    await msg.answer("✅ Ro‘yxatdan o‘tdingiz", reply_markup=kb)

# ================= ADMIN =================
@dp.message_handler(lambda m: m.text == "📊 Admin")
async def admin(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return await msg.answer("❌ Ruxsat yo‘q")

    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    await msg.answer(f"👤 Userlar: {count}")

# ================= IMAGE =================
@dp.message_handler(lambda m: m.text == "🖼 Rasm HD")
async def ask_img(msg: types.Message):
    await msg.answer("Rasm link yuboring")

@dp.message_handler(lambda m: m.text.startswith("http"))
async def get_img(msg: types.Message):
    res = upscale_image(msg.text)
    await msg.answer(res)

# ================= ISLAM =================
@dp.message_handler(lambda m: "islom" in m.text.lower())
async def islam(msg: types.Message):
    await msg.answer(islamic_answer(msg.text))

# ================= CHAT =================
@dp.message_handler()
async def chat(msg: types.Message):
    if is_spam(msg.from_user.id):
        return await msg.answer("⏳ Sekin yozing")

    text = msg.text
    answer = ai_chat(text)
    await msg.answer(answer)

# ================= RUN =================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
