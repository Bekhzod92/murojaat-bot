# Telegram bot: "Dekanga murojaat"
# Talabalar fikr, taklif yoki muammolarni yuborishi mumkin
# Kod Python + python-telegram-bot kutubxonasi asosida yozilgan

from telegram import Update, ForceReply, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import logging
from collections import deque
from datetime import datetime

# --- Logging ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Bosqichlar ---
GET_TOPIC, GET_MESSAGE = range(2)

# --- Admin ID lar ro'yxati ---
admin_chat_ids = [1894112004, 7997871478]

# --- Murojaatchilarni navbat bilan saqlash ---
user_queue = deque()
user_messages = {}

# --- /start komandasi ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [["Ma'naviy-ma'rifiy"], ["O'quv jarayoni"], ["Boshqa mavzu"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        rf"""Assalomu alaykum, {user.first_name}!
Quyidan murojaat mavzusini tanlang:""",
        reply_markup=markup,
    )
    return GET_TOPIC

# --- Mavzu tanlash ---
async def choose_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = update.message.text
    context.user_data['topic'] = topic
    keyboard = [['❌ Bekor qilish']]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Eslatib o'tamizki anonim murojaatlar ko'rib chiqilmaydi! Endi murojaatingiz matnini yozing:",
        reply_markup=markup
    )
    return GET_MESSAGE

# --- Murojaat qabul qilish (talabalar uchun) ---
async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    user = update.effective_user
    vaqt = datetime.now().strftime("%Y-%m-%d %H:%M")
    topic = context.user_data.get('topic', 'Mavzu ko‘rsatilmagan')

    # Talaba yozganda: navbatga qo‘shish
    user_queue.append(user.id)
    user_messages[user.id] = user

    for admin_id in admin_chat_ids:
        await context.bot.send_message(
            chat_id=admin_id,
            text=f"📝 Yangi murojaat ({vaqt}):\n\n👤 {user.full_name} (@{user.username or 'yo‘q'})\n🆔 ID: {user.id}\n📌 Mavzu: {topic}\n\n✉️ Murojaat:\n{message}"
        )

    await update.message.reply_text("Murojaatingiz muvaffaqiyatli yuborildi. Rahmat!", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# --- Admin javobini yuborish ---
async def receive_message_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    user = update.effective_user

    if user.id in admin_chat_ids:
        if user_queue:
            target_user_id = user_queue.popleft()
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"📩 Dekan javobi:\n\n{message}"
                )
                await update.message.reply_text(f"Javob #{target_user_id} foydalanuvchiga yuborildi ✅")
                with open("javoblar_log.txt", "a", encoding="utf-8") as f:
                    f.write(f"To: {target_user_id}\nJavob: {message}\n\n")
            except Exception:
                await update.message.reply_text("❌ Javob yuborilmadi. Xatolik yuz berdi.")
        else:
            await update.message.reply_text("🕑 Hozircha kutayotgan foydalanuvchi yo‘q.")

# --- Statistika ---
async def stat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in admin_chat_ids:
        await update.message.reply_text(f"📊 Navbatda {len(user_queue)} foydalanuvchi bor.")

# --- Bekor qilish ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Murojaat bekor qilindi.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# --- Asosiy dastur ---
if __name__ == '__main__':
    app = ApplicationBuilder().token("8073512777:AAHlk0bWpItH54WJ7SEH3gNFqoSSz4_cKSg").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GET_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_topic)],
            GET_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('stat', stat))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message_admin))
    app.run_polling()
