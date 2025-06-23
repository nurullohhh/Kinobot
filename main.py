import telebot
from telebot import types
import json
import os
import time
from datetime import datetime
from telebot.apihelper import ApiTelegramException
from keep_alive import keep_alive
from config import TOKEN

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
keep_alive()

# 🔒 Mandatory subscription settings
CHANNEL_ID = -2795712385  # Your channel ID
CHANNEL_LINK = "https://t.me/neva_uzz"  # Your channel link
CHANNEL_USERNAME = "@neva_uzz"  # Your channel username

# 📁 File names
ADMINS_FILE = "admins.json"
KINO_FILE = "kino_data.json"
CHANNELS_FILE = "channels.json"

# 📁 Create files if they don't exist
for file in [ADMINS_FILE, KINO_FILE, CHANNELS_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            if file == ADMINS_FILE:
                json.dump({"admins": [], "owner": None}, f)
            elif file == CHANNELS_FILE:
                json.dump({"channels": []}, f)
            else:
                json.dump([], f)

# 👑 Check if user is owner
def is_owner(user_id):
    with open(ADMINS_FILE) as f:
        data = json.load(f)
    return str(user_id) == str(data.get("owner"))

# ✅ Admin panel
def admin_panel():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        "🎬 Kino qo'shish", "❌ Kino o'chirish",
        "📃 Kinolar ro'yxati", "📊 Statistika",
        "➕ Admin qo'shish", "➖ Admin o'chirish",
        "📺 Kanallar", "🔙 Asosiy menyu"
    ]
    markup.add(*buttons)
    return markup

# 👤 User panel
def user_panel():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    buttons = [
        "🎞 Kino olish",
        "📞 Admin bilan bog'lanish"
    ]
    markup.add(*buttons)
    return markup

# 📌 Check if user is admin
def is_admin(user_id):
    with open(ADMINS_FILE) as f:
        data = json.load(f)
    return str(user_id) in data.get("admins", []) or is_owner(user_id)

# 🔍 Check channel subscription
def is_subscribed(user_id):
    try:
        with open(CHANNELS_FILE) as f:
            channels = json.load(f).get("channels", [])
        
        # Always check the main channel
        channels.append({"channel_id": CHANNEL_ID, "channel_link": CHANNEL_LINK})
        
        for channel in channels:
            try:
                member = bot.get_chat_member(channel["channel_id"], user_id)
                if member.status not in ["member", "administrator", "creator"]:
                    return False
            except Exception as e:
                print(f"Error checking channel {channel['channel_id']}: {e}")
                return False
        return True
    except Exception as e:
        print(f"Subscription check error: {e}")
        return False

# 🚪 /start command
@bot.message_handler(commands=["start"])
def start(msg):
    if is_subscribed(msg.from_user.id):
        if is_admin(msg.from_user.id):
            bot.send_message(msg.chat.id, "🔐 Admin paneliga xush kelibsiz!", reply_markup=admin_panel())
        else:
            bot.send_message(msg.chat.id, "👋 Salom! Kino botiga xush kelibsiz!", reply_markup=user_panel())
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📺 Kanalga obuna bo'lish", url=CHANNEL_LINK))
        markup.add(types.InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_subscription"))
        bot.send_message(
            msg.chat.id,
            f"❗ Botdan foydalanish uchun quyidagi kanal(lar)ga obuna bo'ling:\n\n{CHANNEL_USERNAME}",
            reply_markup=markup
        )

# 🔄 Callback query handler for subscription check
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription(call):
    if is_subscribed(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        if is_admin(call.from_user.id):
            bot.send_message(call.message.chat.id, "🔐 Admin paneliga xush kelibsiz!", reply_markup=admin_panel())
        else:
            bot.send_message(call.message.chat.id, "👋 Salom! Kino botiga xush kelibsiz!", reply_markup=user_panel())
    else:
        bot.answer_callback_query(call.id, "❌ Hali ham barcha kanallarga obuna bo'lmagansiz!", show_alert=True)

# 🔙 Return to main menu
@bot.message_handler(func=lambda m: m.text == "🔙 Asosiy menyu")
def main_menu(msg):
    if is_admin(msg.from_user.id):
        bot.send_message(msg.chat.id, "🏠 Asosiy menyu", reply_markup=admin_panel())
    else:
        bot.send_message(msg.chat.id, "🏠 Asosiy menyu", reply_markup=user_panel())

# 🎞 Get movie (User function)
@bot.message_handler(func=lambda m: m.text == "🎞 Kino olish")
def kino_olish(msg):
    if is_subscribed(msg.from_user.id):
        bot.send_message(msg.chat.id, "🔑 Kino kodini kiriting:")
        bot.register_next_step_handler(msg, show_kino)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📺 Kanalga obuna bo'lish", url=CHANNEL_LINK))
        markup.add(types.InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_subscription"))
        bot.send_message(msg.chat.id, "❗ Botdan foydalanish uchun kanalga obuna bo'ling.", reply_markup=markup)

# 🔍 Show movie by code
def show_kino(msg):
    code = msg.text.strip()
    
    with open(KINO_FILE, "r") as f:
        data = json.load(f)
    
    for kino in data:
        if kino["code"] == code:
            kino["views"] += 1
            with open(KINO_FILE, "w") as f:
                json.dump(data, f, indent=2)
            
            bot.send_video(
                msg.chat.id, 
                kino["video_id"], 
                caption=f"🎬 {kino['name']}\n👁 {kino['views']} ta ko'rish\n🤖 @{bot.get_me().username}"
            )
            return
    
    bot.reply_to(msg, "❌ Bunday koddagi kino topilmadi.")

# 📞 Contact admin (User function)
@bot.message_handler(func=lambda m: m.text == "📞 Admin bilan bog'lanish")
def contact_admin(msg):
    bot.send_message(msg.chat.id, "✍️ Xabaringizni yuboring:")
    bot.register_next_step_handler(msg, forward_to_admin)

def forward_to_admin(msg):
    with open(ADMINS_FILE) as f:
        admins = json.load(f)
    
    for admin_id in admins["admins"] + [admins["owner"]]:
        try:
            bot.send_message(
                admin_id,
                f"📬 Yangi xabar!\n\n"
                f"👤 Foydalanuvchi: {msg.from_user.first_name} (@{msg.from_user.username or 'nomalum'})\n"
                f"🆔 ID: {msg.from_user.id}\n\n"
                f"📝 Xabar: {msg.text}"
            )
        except Exception as e:
            print(f"Error sending message to admin {admin_id}: {e}")
    
    bot.send_message(msg.chat.id, "✅ Xabaringiz adminlarga yuborildi!")

# 🎬 Add movie (Admin function)
@bot.message_handler(func=lambda m: m.text == "🎬 Kino qo'shish")
def upload_kino(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "⚠️ Siz admin emassiz!")
        return
    
    bot.send_message(msg.chat.id, "🎥 Kinoni yuboring (.mp4)...")
    bot.register_next_step_handler(msg, save_video)

def save_video(msg):
    if not msg.video:
        bot.reply_to(msg, "❌ Faqat .mp4 video qabul qilinadi.")
        return
    
    bot.send_message(msg.chat.id, "✍ Kino nomi va kodi: (format: kod | nom)")
    bot.register_next_step_handler(msg, lambda m: save_info(m, msg.video.file_id))

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
            "views": 0,
            "added_by": msg.from_user.id,
            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        with open(KINO_FILE, "w") as f:
            json.dump(data, f, indent=2)
        
        bot.send_message(msg.chat.id, f"✅ Saqlandi!\n🎬 {name.strip()}\n🔑 Kod: {code.strip()}")
    except:
        bot.reply_to(msg, "❌ Format xato. To'g'ri yozing: kod | nom")

# 📊 Statistics (Admin function)
@bot.message_handler(func=lambda m: m.text == "📊 Statistika")
def admin_stats(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "⚠️ Siz admin emassiz!")
        return
    
    with open(KINO_FILE) as f:
        data = json.load(f)
    total = len(data)
    views = sum(k["views"] for k in data)
    
    bot.send_message(
        msg.chat.id,
        f"📊 Statistika:\n"
        f"🎬 Kinolar soni: {total}\n"
        f"👁 Umumiy ko'rish: {views}"
    )

# 📃 List movies (Admin function)
@bot.message_handler(func=lambda m: m.text == "📃 Kinolar ro'yxati")
def list_movies(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "⚠️ Siz admin emassiz!")
        return
    
    with open(KINO_FILE) as f:
        data = json.load(f)
    
    if not data:
        bot.reply_to(msg, "ℹ️ Kinolar ro'yxati bo'sh!")
        return
    
    response = "🎬 Kinolar ro'yxati:\n\n"
    for kino in data:
        response += f"🔑 {kino['code']} - {kino['name']} (👁 {kino['views']})\n"
    
    if len(response) > 4000:
        for x in range(0, len(response), 4000):
            bot.send_message(msg.chat.id, response[x:x+4000])
    else:
        bot.send_message(msg.chat.id, response)

# ❌ Delete movie (Admin function)
@bot.message_handler(func=lambda m: m.text == "❌ Kino o'chirish")
def delete_movie(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "⚠️ Siz admin emassiz!")
        return
    
    with open(KINO_FILE) as f:
        data = json.load(f)
    
    if not data:
        bot.reply_to(msg, "ℹ️ Kinolar ro'yxati bo'sh!")
        return
    
    markup = types.InlineKeyboardMarkup()
    for kino in data:
        markup.add(types.InlineKeyboardButton(
            f"❌ {kino['code']} - {kino['name']}", 
            callback_data=f"delete_kino_{kino['code']}"
        ))
    
    bot.send_message(msg.chat.id, "🗑 O'chirish uchun kinoni tanlang:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_kino_"))
def callback_delete_movie(call):
    code = call.data.split("_")[-1]
    with open(KINO_FILE, "r+") as f:
        data = json.load(f)
        data = [k for k in data if k["code"] != code]
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()
    
    bot.edit_message_text(
        f"✅ {code} kodli kino o'chirildi!",
        call.message.chat.id,
        call.message.message_id
    )

# Admin management functions (similar to previous versions)
# ... [keep all your existing admin management functions]

# Error handling for polling
def run_bot():
    while True:
        try:
            print("✅ Bot ishga tushdi...")
            bot.infinity_polling()
        except ApiTelegramException as api_error:
            print(f"Telegram API xatosi: {api_error}")
            time.sleep(10)
        except Exception as e:
            print(f"Kutilmagan xato: {e}")
            time.sleep(30)

if __name__ == "__main__":
    run_bot()
