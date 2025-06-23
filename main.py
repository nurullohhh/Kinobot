import telebot
from telebot import types
import json
import os
from keep_alive import keep_alive

TOKEN = "8063118515:AAFvcV6NmbRH60gLjDyt5lMQKZxOb2AMnko"
bot = telebot.TeleBot(TOKEN)
keep_alive()

# Fayl nomlari
ADMINS_FILE = "admins.json"
KINO_FILE = "kino_data.json"

# 📁 Fayllar mavjudligini tekshiradi
for file in [ADMINS_FILE, KINO_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({} if "admin" in file else [], f)

# 📌 Admin tekshirish
def is_admin(user_id):
    with open(ADMINS_FILE) as f:
        admins = json.load(f)
    return str(user_id) in admins

# 🆔 Add admin command (manual)
@bot.message_handler(commands=["addadmin"])
def add_admin(msg):
    if msg.from_user.id == ADMIN_ID:
        try:
            uid = msg.text.split()[1]
            with open(ADMINS_FILE, "r") as f:
                admins = json.load(f)
            admins[uid] = "on"
            with open(ADMINS_FILE, "w") as f:
                json.dump(admins, f)
            bot.reply_to(msg, f"✅ Admin qo‘shildi: {uid}")
        except:
            bot.reply_to(msg, "❌ Format: /addadmin USER_ID")

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

# 🆘 Start
@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(msg.chat.id, "👋 Salom! Kino ko‘rish uchun /search yozing.")

# 🔄 Doimiy ishlatish
print("✅ Bot ishga tushdi...")
bot.remove_webhook()
bot.infinity_polling()
