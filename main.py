import telebot
from telebot import types
import json
import os
from datetime import datetime, timedelta
from keep_alive import keep_alive

keep_alive()

# 🔑 Sozlamalar
TOKEN = '7226611774:AAEf8Wa1_gB08uR8eroGm8rkOkZQIl49Eng'
ADMIN_IDS = [1936905280, 6566152502]
def is_admin(user_id):
    return user_id in ADMIN_IDS
DATA_FILE = 'kino_data.json'

# Botni ishga tushirish (katta fayllar uchun maxsus sozlamalar)
bot = telebot.TeleBot(TOKEN, parse_mode='HTML', threaded=True, num_threads=10)

# 📂 Ma'lumotlarni yuklash
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Agar 'kanal' kaliti bo'lmasa yoki string bo'lsa
                if 'kanal' not in data:
                    data['kanal'] = []
                elif isinstance(data['kanal'], str):
                    data['kanal'] = [data['kanal']] if data['kanal'] else []
                if 'kinolar' not in data:
                    data['kinolar'] = {}
                if 'statistika' not in data:
                    data['statistika'] = {
                        'umumiy_foydalanuvchilar': [],
                        'oylik_foydalanuvchilar': {},
                        'aktiv_foydalanuvchilar': {}
                    }
                # Set ni listga aylantirish
                if isinstance(data['statistika']['umumiy_foydalanuvchilar'], list):
                    data['statistika']['umumiy_foydalanuvchilar'] = set(data['statistika']['umumiy_foydalanuvchilar'])
                # Oylik foydalanuvchilarni setga aylantirish
                for month in data['statistika']['oylik_foydalanuvchilar']:
                    if isinstance(data['statistika']['oylik_foydalanuvchilar'][month], list):
                        data['statistika']['oylik_foydalanuvchilar'][month] = set(data['statistika']['oylik_foydalanuvchilar'][month])
                # Aktiv foydalanuvchilarni setga aylantirish
                for date in data['statistika']['aktiv_foydalanuvchilar']:
                    if isinstance(data['statistika']['aktiv_foydalanuvchilar'][date], list):
                        data['statistika']['aktiv_foydalanuvchilar'][date] = set(data['statistika']['aktiv_foydalanuvchilar'][date])
                return data
        except Exception as e:
            print(f"Ma'lumotlarni yuklashda xato: {e}")
            return {"kinolar": {}, "kanal": [], "statistika": {
                'umumiy_foydalanuvchilar': set(),
                'oylik_foydalanuvchilar': {},
                'aktiv_foydalanuvchilar': {}
            }}
    return {"kinolar": {}, "kanal": [], "statistika": {
        'umumiy_foydalanuvchilar': set(),
        'oylik_foydalanuvchilar': {},
        'aktiv_foydalanuvchilar': {}
    }}

# 📂 Ma'lumotlarni saqlash
def save_data(data):
    # Set ni listga aylantirish
    data_to_save = {
        'kinolar': data['kinolar'],
        'kanal': data['kanal'],
        'statistika': {
            'umumiy_foydalanuvchilar': list(data['statistika']['umumiy_foydalanuvchilar']),
            'oylik_foydalanuvchilar': {},
            'aktiv_foydalanuvchilar': {}
        }
    }
    
    # Oylik foydalanuvchilarni listga aylantirish
    for month in data['statistika']['oylik_foydalanuvchilar']:
        data_to_save['statistika']['oylik_foydalanuvchilar'][month] = list(data['statistika']['oylik_foydalanuvchilar'][month])
    
    # Aktiv foydalanuvchilarni listga aylantirish
    for date in data['statistika']['aktiv_foydalanuvchilar']:
        data_to_save['statistika']['aktiv_foydalanuvchilar'][date] = list(data['statistika']['aktiv_foydalanuvchilar'][date])
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

# 📊 Ma'lumotlarni yuklab olamiz
data = load_data()
kino_dict = data["kinolar"]
CHANNELS = data["kanal"]
statistika = data["statistika"]

# 📈 Statistika yangilash
def update_statistics(user_id):
    # Umumiy foydalanuvchilar
    if not isinstance(statistika['umumiy_foydalanuvchilar'], set):
        statistika['umumiy_foydalanuvchilar'] = set(statistika['umumiy_foydalanuvchilar'])
    statistika['umumiy_foydalanuvchilar'].add(user_id)
    
    # Oylik foydalanuvchilar
    current_month = datetime.now().strftime("%Y-%m")
    if current_month not in statistika['oylik_foydalanuvchilar']:
        statistika['oylik_foydalanuvchilar'][current_month] = set()
    elif not isinstance(statistika['oylik_foydalanuvchilar'][current_month], set):
        statistika['oylik_foydalanuvchilar'][current_month] = set(statistika['oylik_foydalanuvchilar'][current_month])
    statistika['oylik_foydalanuvchilar'][current_month].add(user_id)
    
    # Aktiv foydalanuvchilar (so'ngi 30 kun)
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in statistika['aktiv_foydalanuvchilar']:
        statistika['aktiv_foydalanuvchilar'][today] = set()
    elif not isinstance(statistika['aktiv_foydalanuvchilar'][today], set):
        statistika['aktiv_foydalanuvchilar'][today] = set(statistika['aktiv_foydalanuvchilar'][today])
    statistika['aktiv_foydalanuvchilar'][today].add(user_id)
    
    # Eski ma'lumotlarni tozalash (30 kundan oldingi aktiv foydalanuvchilar)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    dates_to_remove = []
    for date_str in statistika['aktiv_foydalanuvchilar']:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        if date < thirty_days_ago:
            dates_to_remove.append(date_str)
    for date_str in dates_to_remove:
        del statistika['aktiv_foydalanuvchilar'][date_str]
    
    save_data(data)

# 📊 Statistika ko'rsatish
def get_statistics():
    # Aktiv foydalanuvchilar (so'ngi 30 kun)
    active_users = set()
    for day_users in statistika['aktiv_foydalanuvchilar'].values():
        active_users.update(day_users)
    
    # Oylik foydalanuvchilar (joriy oy)
    current_month = datetime.now().strftime("%Y-%m")
    monthly_users = len(statistika['oylik_foydalanuvchilar'].get(current_month, set()))
    
    return {
        'umumiy': len(statistika['umumiy_foydalanuvchilar']),
        'oylik': monthly_users,
        'aktiv': len(active_users)
    }

# 🧪 Obuna tekshiradi
def check_subscription(user_id):
    if not CHANNELS:
        return True
        
    for channel in CHANNELS:
        try:
            chat = bot.get_chat(channel)
            member = bot.get_chat_member(chat.id, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            print(f"Obuna tekshirishda xato (kanal: {channel}): {e}")
            continue
    return True

# 👨‍💻 Admin tekshiruvi
def is_admin(user_id):
    return user_id in ADMIN_IDS

# 🚪 /start buyrug'i
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    update_statistics(user_id)  # Statistika yangilash
    
    if not check_subscription(user_id):
        show_subscription_request(message)
        return
    
    if is_admin(user_id):
        admin_panel(message)
    else:
        show_movies(message)

def show_subscription_request(message):
    markup = types.InlineKeyboardMarkup()
    for channel in CHANNELS:
        try:
            chat = bot.get_chat(channel)
            markup.add(types.InlineKeyboardButton(
                f"✅ {chat.title} kanaliga obuna bo'lish", 
                url=f"https://t.me/{channel[1:]}")
            )
        except Exception as e:
            print(f"Kanal ma'lumotlarini olishda xato: {e}")
            continue
            
    markup.add(types.InlineKeyboardButton(
        "✅ Obunani tekshirish", 
        callback_data="check_subscription")
    )
    
    channels_text = "\n".join([f"- {ch}" for ch in CHANNELS])
    bot.send_message(
        message.chat.id,
        f"⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:\n{channels_text}",
        reply_markup=markup
    )

# 🔄 Obunani tekshirish
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_sub_callback(call):
    user_id = call.from_user.id
    if check_subscription(user_id):
        if is_admin(user_id):
            admin_panel(call.message)
        else:
            show_movies(call.message)
        bot.answer_callback_query(call.id, "✅ Obuna tasdiqlandi!")
    else:
        bot.answer_callback_query(call.id, "❌ Hali obuna bo'lmagansiz!", show_alert=True)

# � Admin paneli
def admin_panel(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        "🎬 Kino qo'shish (2GB gacha)",
        "🗑 Kino o'chirish",
        "📋 Kinolar ro'yxati",
        "📢 Kanallar boshqaruvi",
        "📊 Statistika",
        "👥 Foydalanuvchi menyusi"
    ]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "👨‍💻 <b>Admin Panel</b>", reply_markup=markup)

# 📊 Statistika
@bot.message_handler(func=lambda message: message.text == "📊 Statistika" and is_admin(message.from_user.id))
def show_statistics(message):
    stats = get_statistics()
    bot.send_message(
        message.chat.id,
        f"📊 <b>Bot statistikasi:</b>\n\n"
        f"👥 Umumiy foydalanuvchilar: <b>{stats['umumiy']}</b>\n"
        f"📅 Oylik foydalanuvchilar: <b>{stats['oylik']}</b>\n"
        f"🔄 Aktiv foydalanuvchilar (30 kun): <b>{stats['aktiv']}</b>"
    )

# 📢 Kanallar boshqaruvi
@bot.message_handler(func=lambda message: message.text == "📢 Kanallar boshqaruvi" and is_admin(message.from_user.id))
def manage_channels(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("➕ Kanal qo'shish"),
        types.KeyboardButton("➖ Kanal o'chirish"),
        types.KeyboardButton("📋 Ulangan kanallar"),
        types.KeyboardButton("🔙 Orqaga")
    )
    bot.send_message(message.chat.id, "📢 <b>Kanallar boshqaruvi</b>\nKerakli amalni tanlang:", reply_markup=markup)

# ➕ Kanal qo'shish
@bot.message_handler(func=lambda message: message.text == "➕ Kanal qo'shish" and is_admin(message.from_user.id))
def add_channel(message):
    msg = bot.send_message(
        message.chat.id, 
        "📢 Yangi kanal username'ini yuboring (@ belgisi bilan):\n\nMasalan: @yangi_kanal",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, process_add_channel)

def process_add_channel(message):
    global CHANNELS, data
    new_channel = message.text.strip().lower()
    
    if not new_channel.startswith('@'):
        bot.send_message(message.chat.id, "❌ Kanal username @ belgisi bilan boshlanishi kerak!")
        manage_channels(message)
        return
    
    if new_channel in CHANNELS:
        bot.send_message(message.chat.id, "❌ Bu kanal allaqachon qo'shilgan!")
        manage_channels(message)
        return
    
    try:
        # Kanal mavjudligini tekshirish
        chat = bot.get_chat(new_channel)
        
        # Bot kanalda adminligini tekshirish
        bot_member = bot.get_chat_member(chat.id, bot.get_me().id)
        if bot_member.status not in ['administrator', 'creator']:
            raise Exception("Bot kanalda admin emas")
        
        # Ma'lumotlarni yangilaymiz
        CHANNELS.append(new_channel)
        data["kanal"] = CHANNELS
        save_data(data)
        
        bot.send_message(
            message.chat.id, 
            f"✅ Kanal muvaffaqiyatli qo'shildi!\n<b>Kanal:</b> {new_channel}\n<b>Nomi:</b> {chat.title}"
        )
    except Exception as e:
        bot.send_message(
            message.chat.id, 
            f"❌ Xato: {str(e)}\n\nKanal topilmadi yoki bot admin emas. Iltimos, tekshirib qayta urinib ko'ring."
        )
    
    manage_channels(message)

# ➖ Kanal o'chirish

@bot.message_handler(func=lambda message: message.text == "➖ Kanal o'chirish" and is_admin(message.from_user.id))
def remove_channel(message):
    if not CHANNELS:
        bot.send_message(message.chat.id, "❌ O'chirish uchun kanal mavjud emas.")
        manage_channels(message)
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for channel in CHANNELS:
        try:
            chat = bot.get_chat(channel)
            markup.add(types.KeyboardButton(f"{channel} ({chat.title})"))
        except:
            markup.add(types.KeyboardButton(channel))
    
    markup.add(types.KeyboardButton("🔙 Orqaga"))
    
    msg = bot.send_message(
        message.chat.id, 
        "❌ O'chirish uchun kanalni tanlang:", 
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_remove_channel)

def process_remove_channel(message):
    global CHANNELS, data
    
    if message.text == "🔙 Orqaga":
        manage_channels(message)
        return
        
    # Faqat kanal username'ini ajratib olamiz
    channel = message.text.split()[0] if ' ' in message.text else message.text
    channel = channel.lower()
    
    if channel in CHANNELS:
        CHANNELS.remove(channel)
        data["kanal"] = CHANNELS
        save_data(data)
        bot.send_message(message.chat.id, f"✅ {channel} kanali o'chirildi!")
    else:
        bot.send_message(message.chat.id, "❌ Bunday kanal topilmadi.")
    
    manage_channels(message)

# 📋 Ulangan kanallar
@bot.message_handler(func=lambda message: message.text == "📋 Ulangan kanallar" and is_admin(message.from_user.id))
def list_channels(message):
    if not CHANNELS:
        bot.send_message(message.chat.id, "❌ Ulangan kanallar mavjud emas.")
    else:
        channels_info = []
        for channel in CHANNELS:
            try:
                chat = bot.get_chat(channel)
                channels_info.append(f"• {channel} (<b>{chat.title}</b>)")
            except:
                channels_info.append(f"• {channel} (mavjud emas)")
        
        bot.send_message(
            message.chat.id,
            "📋 <b>Ulangan kanallar:</b>\n" + "\n".join(channels_info)
        )
    manage_channels(message)

# 🔙 Orqaga
@bot.message_handler(func=lambda message: message.text == "🔙 Orqaga" and is_admin(message.from_user.id))
def back_to_admin_panel(message):
    admin_panel(message)

# 🎬 Kino qo'shish (2GB gacha videolar uchun optimallashtirilgan)
@bot.message_handler(func=lambda message: message.text == "🎬 Kino qo'shish (2GB gacha)" and is_admin(message.from_user.id))
def add_movie_start(message):
    msg = bot.send_message(
        message.chat.id,
        "🎥 <b>Kino qo'shish</b>\n\nKino kodini yuboring (masalan: <code>001</code>):",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(msg, process_movie_code)

def process_movie_code(message):
    try:
        code = message.text.strip()
        if code in kino_dict:
            bot.send_message(message.chat.id, "❌ Bu kod allaqachon mavjud!")
            return admin_panel(message)
            
        msg = bot.send_message(message.chat.id, "📝 Kino nomini yuboring:")
        bot.register_next_step_handler(msg, lambda m: process_movie_name(m, code))
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Xato: {str(e)}")
        admin_panel(message)

def process_movie_name(message, code):
    try:
        name = message.text.strip()
        msg = bot.send_message(
            message.chat.id,
            "📤 Kino kontentini yuboring:\n\n"
            "• Video fayli (2GB gacha)\n"
            "• Yoki havolani matn shaklida",
            reply_markup=types.ForceReply(selective=True)
        )
        bot.register_next_step_handler(msg, lambda m: process_movie_content(m, code, name))
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Xato: {str(e)}")
        admin_panel(message)

def process_movie_content(message, code, name):
    try:
        if message.content_type == 'text':
            # Havola bilan kino
            url = message.text.strip()
            kino_dict[code] = {
                "nomi": name,
                "havola": url,
                "tur": "link"
            }
            bot.send_message(message.chat.id, f"✅ Kino qo'shildi!\n<b>Kod:</b> <code>{code}</code>\n<b>Nomi:</b> {name}")
            
        elif message.content_type == 'video':
            # Video bilan kino (2GB gacha)
            video = message.video
            
            # Video ma'lumotlarini saqlaymiz
            kino_dict[code] = {
                "nomi": name,
                "file_id": video.file_id,
                "file_unique_id": video.file_unique_id,
                "tur": "video",
                "width": video.width,
                "height": video.height,
                "duration": video.duration,
                "file_size": video.file_size
            }
            
            bot.send_message(
                message.chat.id,
                f"✅ Kino qo'shildi!\n<b>Kod:</b> <code>{code}</code>\n"
                f"<b>Nomi:</b> {name}\n"
                f"<b>Hajmi:</b> {video.file_size//(1024*1024)}MB\n"
                f"<b>Davomiylik:</b> {video.duration} soniya"
            )
        
        data["kinolar"] = kino_dict
        save_data(data)
        
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Xato yuz berdi: {str(e)}")
    
    admin_panel(message)

# 🗑 Kino o'chirish
@bot.message_handler(func=lambda message: message.text == "🗑 Kino o'chirish" and is_admin(message.from_user.id))
def delete_movie_start(message):
    if not kino_dict:
        bot.send_message(message.chat.id, "❌ O'chirish uchun kino mavjud emas.")
        admin_panel(message)
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [types.KeyboardButton(code) for code in kino_dict.keys()]
    markup.add(*buttons)
    markup.add(types.KeyboardButton("🔙 Orqaga"))
    
    msg = bot.send_message(
        message.chat.id,
        "❌ O'chirish uchun kino kodini tanlang:",
        reply_markup=markup
    )
    bot.register_next_step_handler(msg, process_movie_delete)

def process_movie_delete(message):
    if message.text == "🔙 Orqaga":
        admin_panel(message)
        return
    
    code = message.text
    if code in kino_dict:
        del kino_dict[code]
        data["kinolar"] = kino_dict
        save_data(data)
        bot.send_message(message.chat.id, f"✅ {code} kodli kino o'chirildi!")
    else:
        bot.send_message(message.chat.id, "❌ Bunday kodli kino topilmadi.")
    
    admin_panel(message)

# 📋 Kinolar ro'yxati
@bot.message_handler(func=lambda message: message.text == "📋 Kinolar ro'yxati" and is_admin(message.from_user.id))
def list_movies(message):
    if not kino_dict:
        bot.send_message(message.chat.id, "❌ Kinolar ro'yxati bo'sh.")
    else:
        movies_list = []
        for code, info in kino_dict.items():
            if info['tur'] == 'link':
                movies_list.append(f"<code>{code}</code>: {info['nomi']} (havola)")
            else:
                size = info.get('file_size', 0) // (1024*1024)
                movies_list.append(f"<code>{code}</code>: {info['nomi']} ({size}MB)")
        
        bot.send_message(
            message.chat.id,
            "📋 <b>Kinolar ro'yxati:</b>\n\n" + "\n".join(movies_list)
        )
    admin_panel(message)

# 👥 Foydalanuvchi menyusi
@bot.message_handler(func=lambda message: message.text == "👥 Foydalanuvchi menyusi" and is_admin(message.from_user.id))
def user_menu(message):
    show_movies(message)

def show_movies(message):
    if not kino_dict:
        bot.send_message(message.chat.id, "❌ Hozircha kinolar mavjud emas.")

    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    buttons = [types.KeyboardButton(code) for code in kino_dict.keys()]
    markup.add(*buttons)
    
    bot.send_message(
        message.chat.id,
        "🎬 <b>Kino kodini tanlang:</b>",
        reply_markup=markup
    )
if __name__ == "__main__":
    print("🤖 Bot ishga tushdi...")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
