import telebot
from telebot import types
import json
import os
from datetime import datetime
from keep_alive import keep_alive
from config import TOKEN

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
keep_alive()

# 🔒 Mandatory subscription settings
CHANNEL_ID = -1001234567890  # Your channel ID
CHANNEL_LINK = "https://t.me/YOUR_CHANNEL_USERNAME"  # Your channel link
CHANNEL_USERNAME = "@YOUR_CHANNEL_USERNAME"  # Your channel username

# 📁 File names
ADMINS_FILE = "admins.json"
KINO_FILE = "kino_data.json"
CHANNELS_FILE = "channels.json"
USERS_FILE = "users.json"

# 📁 Create files if they don't exist
for file in [ADMINS_FILE, KINO_FILE, CHANNELS_FILE, USERS_FILE]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            if file == ADMINS_FILE:
                json.dump({"admins": [], "owner": None}, f)
            elif file == CHANNELS_FILE:
                json.dump({"channels": []}, f)
            elif file == USERS_FILE:
                json.dump({"users": {}}, f)
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
        "👥 Foydalanuvchilar", "📢 Xabar yuborish",
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
        "📊 Bot statistikasi",
        "📞 Admin bilan bog'lanish"
    ]
    markup.add(*buttons)
    return markup

# 📌 Check if user is admin
def is_admin(user_id):
    with open(ADMINS_FILE) as f:
        data = json.load(f)
    return str(user_id) in data.get("admins", []) or is_owner(user_id)

# 👤 Register or update user
def register_user(user):
    with open(USERS_FILE, "r+") as f:
        data = json.load(f)
        user_id = str(user.id)
        if user_id not in data["users"]:
            data["users"][user_id] = {
                "first_name": user.first_name,
                "last_name": user.last_name or "",
                "username": user.username or "",
                "join_date": str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                "last_active": str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                "movies_watched": 0
            }
        else:
            data["users"][user_id]["last_active"] = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()

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
    register_user(msg.from_user)
    
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
    register_user(msg.from_user)
    
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
    register_user(msg.from_user)
    code = msg.text.strip()
    
    with open(KINO_FILE, "r") as f:
        data = json.load(f)
    
    for kino in data:
        if kino["code"] == code:
            kino["views"] += 1
            with open(KINO_FILE, "w") as f:
                json.dump(data, f, indent=2)
            
            # Update user stats
            with open(USERS_FILE, "r+") as f:
                users_data = json.load(f)
                user_id = str(msg.from_user.id)
                if user_id in users_data["users"]:
                    users_data["users"][user_id]["movies_watched"] += 1
                f.seek(0)
                json.dump(users_data, f, indent=2)
                f.truncate()
            
            bot.send_video(
                msg.chat.id, 
                kino["video_id"], 
                caption=f"🎬 {kino['name']}\n👁 {kino['views']} ta ko'rish\n🤖 @{bot.get_me().username}"
            )
            return
    
    bot.reply_to(msg, "❌ Bunday koddagi kino topilmadi.")

# 📊 Bot statistics (User function)
@bot.message_handler(func=lambda m: m.text == "📊 Bot statistikasi")
def user_stats(msg):
    register_user(msg.from_user)
    
    with open(KINO_FILE) as f:
        movies = json.load(f)
    
    with open(USERS_FILE) as f:
        users = json.load(f)
    
    total_movies = len(movies)
    total_views = sum(m["views"] for m in movies)
    total_users = len(users["users"])
    
    bot.send_message(
        msg.chat.id,
        f"📊 Bot statistikasi:\n\n"
        f"🎬 Jami kinolar: {total_movies}\n"
        f"👁 Jami ko'rishlar: {total_views}\n"
        f"👥 Jami foydalanuvchilar: {total_users}"
    )

# 📞 Contact admin (User function)
@bot.message_handler(func=lambda m: m.text == "📞 Admin bilan bog'lanish")
def contact_admin(msg):
    register_user(msg.from_user)
    bot.send_message(msg.chat.id, "✍️ Xabaringizni yozib qoldiring va adminlar tez orada siz bilan bog'lanishadi:")
    bot.register_next_step_handler(msg, forward_to_admin)

def forward_to_admin(msg):
    with open(ADMINS_FILE) as f:
        admins = json.load(f)
    
    for admin_id in admins["admins"] + [admins["owner"]]:
        try:
            bot.send_message(
                admin_id,
                f"📬 Yangi xabar!\n\n"
                f"👤 Foydalanuvchi: {msg.from_user.first_name} (@{msg.from_user.username or 'noma'lum'})\n"
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
        movies = json.load(f)
    
    with open(USERS_FILE) as f:
        users = json.load(f)
    
    total_movies = len(movies)
    total_views = sum(m["views"] for m in movies)
    total_users = len(users["users"])
    
    # Get active users (last 30 days)
    active_users = 0
    for user_id, user_data in users["users"].items():
        last_active = datetime.strptime(user_data["last_active"], "%Y-%m-%d %H:%M:%S")
        if (datetime.now() - last_active).days <= 30:
            active_users += 1
    
    bot.send_message(
        msg.chat.id,
        f"📊 Statistika:\n\n"
        f"🎬 Jami kinolar: {total_movies}\n"
        f"👁 Jami ko'rishlar: {total_views}\n"
        f"👥 Jami foydalanuvchilar: {total_users}\n"
        f"🟢 Faol foydalanuvchilar (30 kun): {active_users}"
    )

# 👥 List users (Admin function)
@bot.message_handler(func=lambda m: m.text == "👥 Foydalanuvchilar")
def list_users(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "⚠️ Siz admin emassiz!")
        return
    
    with open(USERS_FILE) as f:
        users = json.load(f)
    
    total_users = len(users["users"])
    today = datetime.now().strftime("%Y-%m-%d")
    new_today = sum(1 for u in users["users"].values() if u["join_date"].startswith(today))
    
    bot.send_message(
        msg.chat.id,
        f"👥 Foydalanuvchilar:\n\n"
        f"🔢 Jami: {total_users}\n"
        f"🆕 Bugun qo'shilgan: {new_today}\n\n"
        f"📊 To'liq ma'lumot olish uchun /users buyrug'ini yuboring"
    )

@bot.message_handler(commands=["users"])
def full_users_list(msg):
    if not is_admin(msg.from_user.id):
        return
    
    with open(USERS_FILE) as f:
        users = json.load(f)
    
    response = "👥 Foydalanuvchilar ro'yxati:\n\n"
    for user_id, user_data in users["users"].items():
        response += (
            f"👤 {user_data['first_name']} {user_data['last_name']}\n"
            f"🆔 ID: {user_id}\n"
            f"📅 Qo'shilgan: {user_data['join_date']}\n"
            f"🔄 So'ngi faollik: {user_data['last_active']}\n"
            f"🎬 Ko'rgan kinolar: {user_data.get('movies_watched', 0)}\n"
            f"————————————\n"
        )
    
    # Split long messages
    for x in range(0, len(response), 4000):
        bot.send_message(msg.chat.id, response[x:x+4000])

# 📢 Send broadcast (Admin function)
@bot.message_handler(func=lambda m: m.text == "📢 Xabar yuborish")
def broadcast(msg):
    if not is_admin(msg.from_user.id):
        bot.reply_to(msg, "⚠️ Siz admin emassiz!")
        return
    
    bot.send_message(msg.chat.id, "✍️ Hammaga yubormoqchi bo'lgan xabaringizni yuboring:")
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(msg):
    with open(USERS_FILE) as f:
        users = json.load(f)
    
    total = len(users["users"])
    success = 0
    failed = 0
    
    bot.send_message(msg.chat.id, f"⏳ Xabar {total} ta foydalanuvchiga yuborilmoqda...")
    
    for user_id in users["users"]:
        try:
            bot.copy_message(user_id, msg.chat.id, msg.message_id)
            success += 1
        except Exception as e:
            print(f"Error sending to {user_id}: {e}")
            failed += 1
    
    bot.send_message(
        msg.chat.id,
        f"✅ Xabar yuborildi!\n\n"
        f"✔️ Muvaffaqiyatli: {success}\n"
        f"✖️ Xatolik: {failed}"
    )

# (The rest of your admin functions like add/remove admin, channels, etc. would go here)
# (They would be similar to the previous version but with the new user tracking system)

print("✅ Bot ishga tushdi...")
bot.infinity_polling()
