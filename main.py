import telebot
from telebot import types
import json
import os
from keep_alive import keep_alive
from config import TOKEN

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
keep_alive()

# 📁 Fayl nomlari
ADMINS_FILE = "admins.json"
KINO_FILE = "kino_data.json"

# 📁 Fayllar mavjudligini tekshiradi
for file in [ADMINS_FILE, KINO_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({} if "admin" in file else [], f)

# ✅ Admin panel
def admin_panel():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🎬 Kino qo‘shish", "❌ Kino o‘chirish")
    markup.row("📃 Kinolar ro‘yxati", "📊 Statistika")
    markup.row("➕ Admin qo‘shish", "➖ Admin o‘chirish")
    markup.row("👥 Adminlar", "📺 Kanallar")
    return markup

# 👤 Foydalanuvchi panel
def user_panel():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🎞 Kino olish")
    return markup

# 📌 Admin tekshirish
def is_admin(user_id):
    with open(ADMINS_FILE) as f:
        admins = json.load(f)
    return str(user_id) in admins

# /start komandasi
@bot.message_handler(commands=["start"])
def start(msg):
    if is_admin(msg.from_user.id):
        bot.send_message(msg.chat.id, "🔐 Admin paneliga xush kelibsiz!", reply_markup=admin_panel())
    else:
        bot.send_message(msg.chat.id, "👋 Salom! Kino botiga xush kelibsiz!", reply_markup=user_panel())

# 🎞 Kino olish tugmasi
@bot.message_handler(func=lambda m: m.text == "🎞 Kino olish")
def kino_olish(msg):
    bot.send_message(msg.chat.id, "🔑 Kino kodini kiriting:")
    bot.register_next_step_handler(msg, show_kino)

# 🎬 Kino yuklash (faqat admin)
@bot.message_handler(commands=["upload"])
def upload_kino(msg):
    if is_admin(msg.from_user.id):
        bot.send_message(msg.chat.id, "🎥 Kinoni yuboring (.mp4)...")
        bot.register_next_step_handler(msg, save_video)
    else:
        bot.reply_to(msg, "⚠️ Siz admin emassiz.")

def save_video(msg):
    if not msg.video:
        bot.reply_to(msg, "❌ Faqat .mp4 video qabul qilinadi.")
        return
    video_id = msg.video.file_id
    bot.send_message(msg.chat.id, "✍ Kino nomi va kodi: (format: kod | nom)")
    bot.register_next_step_handler(msg, lambda m: save_info(m, video_id))

def save_info(msg, video_id):
    try:
        code, name = msg.text.split("|")
        with open(KINO_FILE, "r") as f:
            data = json.load(f)
        for kino in data:
            if kino["code"].strip() == code.strip():
                bot.reply_to(msg, "⚠️ Bu kod allaqachon mavjud!")
                return
        data.append({
            "code": code.strip(),
            "name": name.strip(),
            "video_id": video_id,
            "views": 0
        })
        with open(KINO_FILE, "w") as f:
            json.dump(data, f, indent=2)
        bot.send_message(msg.chat.id, f"✅ Saqlandi!\n🎬 {name.strip()}\n🔑 Kod: {code.strip()}")
    except:
        bot.reply_to(msg, "❌ Format xato. To‘g‘ri yozing: kod | nom")

# 🔎 Kino izlash
@bot.message_handler(commands=["search"])
def search(msg):
    bot.send_message(msg.chat.id, "🔍 Kino kodini kiriting:")
    bot.register_next_step_handler(msg, show_kino)

def show_kino(msg):
    code = msg.text.strip()
    with open(KINO_FILE, "r") as f:
        data = json.load(f)
    for kino in data:
        if kino["code"] == code:
            kino["views"] += 1
            with open(KINO_FILE, "w") as f:
                json.dump(data, f, indent=2)
            bot.send_video(msg.chat.id, kino["video_id"], caption=f"🎬 {kino['name']}\n👁 {kino['views']} ta ko‘rish\n🤖 @{bot.get_me().username}")
            return
    bot.reply_to(msg, "❌ Bunday koddagi kino topilmadi.")

# 📊 Statistika
@bot.message_handler(commands=["stats"])
def stats(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "⚠️ Siz admin emassiz.")
        return
    with open(KINO_FILE) as f:
        data = json.load(f)
    total = len(data)
    views = sum(k["views"] for k in data)
    bot.send_message(msg.chat.id, f"📊 Statistika:\n🎬 Kinolar soni: {total}\n👁 Umumiy ko‘rish: {views}")

print("✅ Bot ishga tushdi...")
bot.infinity_polling()
