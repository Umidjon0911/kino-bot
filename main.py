import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from aiogram.filters import Command, Filter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
BOT_TOKEN = "7992004388:AAHXs5iraV1tcTbUCZZBO7h7FvyDE0oMZNs"
ADMIN_ID=1101514656
Kanal_id= -1002045640831
# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Kanalga obuna tekshiruvi
class CheksupChanel(Filter):
    async def __call__(self, message: Message, bot: Bot):
        status = await bot.get_chat_member(Kanal_id, message.from_user.id)
        return status.status not in ['creator', 'administrator', 'member']

@dp.message(CheksupChanel())
async def obuna_check(message: Message):
    link = 'https://t.me/ParsifalPubg'
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='📢 Kanalga obuna bo‘lish', url=link)]
        ]
    )
    await message.answer(
        "❗ Botdan foydalanish uchun avval kanalga obuna bo‘ling.",
        reply_markup=markup
    )

# SQLite baza
conn = sqlite3.connect("movies.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    name TEXT,
    file_id TEXT,
    description TEXT
)
""")
conn.commit()

# Admin uchun menyu
admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎬 Yangi kino yuklash")],
        [KeyboardButton(text="🎞 Mavjud kinolar")]
    ],
    resize_keyboard=True
)

# Holatlar guruhi
class AddMovie(StatesGroup):
    waiting_for_code = State()
    waiting_for_name = State()
    waiting_for_video = State()
    waiting_for_description = State()

# Start komandasi
@dp.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("👋 Xush kelibsiz, admin!", reply_markup=admin_menu)
    else:
        await message.answer("👋 Xush kelibsiz!\nIltimos, kino kodini yuboring.")

# Kino qo‘shish
@dp.message(F.text == "🎬 Yangi kino yuklash")
async def add_movie_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🎟 Kino kodi?")
    await state.set_state(AddMovie.waiting_for_code)

@dp.message(AddMovie.waiting_for_code)
async def add_movie_code(message: Message, state: FSMContext):
    code = message.text.strip()
    cursor.execute("SELECT * FROM movies WHERE code = ?", (code,))
    if cursor.fetchone():
        return await message.answer("❌ Bu kod mavjud. Yangi kod kiriting.")
    await state.update_data(code=code)
    await message.answer("🎞 Kino nomi?")
    await state.set_state(AddMovie.waiting_for_name)

@dp.message(AddMovie.waiting_for_name)
async def add_movie_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("📹 Video faylni yuboring:")
    await state.set_state(AddMovie.waiting_for_video)

@dp.message(AddMovie.waiting_for_video)
async def add_movie_video(message: Message, state: FSMContext):
    if not message.video:
        return await message.answer("❗ Iltimos, faqat video yuboring.")
    await state.update_data(file_id=message.video.file_id)
    await message.answer("📝 Tavsif kiriting:")
    await state.set_state(AddMovie.waiting_for_description)

@dp.message(AddMovie.waiting_for_description)
async def add_movie_description(message: Message, state: FSMContext):
    data = await state.get_data()
    code = data["code"]
    name = data["name"]
    file_id = data["file_id"]
    description = message.text.strip()

    cursor.execute("INSERT INTO movies (code, name, file_id, description) VALUES (?, ?, ?, ?)",
                   (code, name, file_id, description))
    conn.commit()

    await message.answer(f"✅ Kino saqlandi!\nKod: {code}\nNomi: {name}")
    await state.clear()

# Mavjud kinolar
@dp.message(F.text == "🎞 Mavjud kinolar")
async def show_movies(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    cursor.execute("SELECT code, name FROM movies")
    movies = cursor.fetchall()
    if not movies:
        return await message.answer("📭 Hech qanday kino mavjud emas.")
    
    text = "🎞 Mavjud kinolar:\n\n"
    for code, name in movies:
        text += f"Kod: {code}\nNomi: {name}\n\n"
    await message.answer(text)

# Foydalanuvchi kod yuborganida
@dp.message()
async def handle_user_code(message: Message):
    url = "t.me/Filmtomosha_bot"
    url1 ="t.me/ParsifalPubg"
    if message.from_user.id == ADMIN_ID:
        return
    code = message.text.strip()
    cursor.execute("SELECT name, file_id, description FROM movies WHERE code = ?", (code,))
    result = cursor.fetchone()
    if result:
        name, file_id, description = result
        await message.answer_video(
            file_id,
            caption=f"<b>🎞Film nomi</b>{name} \n\n<b>📽Film haqida malumot </b> \n{description}\n\n<b>Ushbu film</b>👉👇<a href='{url}'>Kinolar</a>👈👈 boti orqali yuklab olindi \nBizning hamkor: <a href='{url1}'>Parsifal Pubg</a> kanali")
        )
    else:
        await message.answer("❌ Bunday kod topilmadi.")

# Ishga tushirish
async def main():
    logger.info("✅ Bot ishga tushdi")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
