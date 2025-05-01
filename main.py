import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, Filter
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import BOT_TOKEN, ADMIN_ID, Kanal_id

# Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Bot
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


class CheksupChanel(Filter):
  async def __call__(self,message:Message,bot:Bot):
    user_ststus=await bot.get_chat_member(Kanal_id,message.from_user.id)
    if user_ststus.status in ['creator','administrator','member']:
      return False
    return True


@dp.message(CheksupChanel())
async def obuna1(message:Message):
  Kanal_link = 't.me/majburiyobunabolasan'
  kanallar=InlineKeyboardMarkup(
   inline_keyboard=[
     [InlineKeyboardButton(text='OBUNA BOLING ',url=Kanal_link)]
   ]
 )
  await message.answer_photo(photo='https://i.ytimg.com/vi/ba7iCce118Y/maxresdefault.jpg',caption='Iltimos kanalga obuna boling',reply_markup=kanallar)



# SQLite bazani ulash
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

# Klaviatura
admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎬 Yangi kino yuklash")],
        [KeyboardButton(text="🎞 Mavjud kinolar")]
    ],
    resize_keyboard=True
)

# State
class AddMovie(StatesGroup):
    waiting_for_code = State()
    waiting_for_name = State()
    waiting_for_video = State()
    waiting_for_description = State()

# /start buyrug'i
@dp.message(Command("start"))
async def start_handler(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("👋 Xush kelibsiz, admin!", reply_markup=admin_menu)
    else:
        await message.answer("👋 Xush kelibsiz!\n🎟 Iltimos, kino kodini yuboring.")

# Yangi kino yuklash
@dp.message(F.text == "🎬 Yangi kino yuklash")
async def process_add_movie(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🎟 Avvalo, kino uchun kodni kiriting:")
    await state.set_state(AddMovie.waiting_for_code)

@dp.message(AddMovie.waiting_for_code)
async def get_code(message: Message, state: FSMContext):
    code = message.text.strip()
    cursor.execute("SELECT * FROM movies WHERE code = ?", (code,))
    if cursor.fetchone():
        return await message.answer("❌ Bu kod allaqachon mavjud. Boshqa kod kiriting.")
    await state.update_data(code=code)
    await message.answer("🎞 Endi kino nomini yuboring:")
    await state.set_state(AddMovie.waiting_for_name)

@dp.message(AddMovie.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name)
    await message.answer("📹 Endi video faylini yuboring:")
    await state.set_state(AddMovie.waiting_for_video)

@dp.message(AddMovie.waiting_for_video)
async def get_video(message: Message, state: FSMContext):
    if not message.video:
        return await message.answer("❗ Iltimos, video faylni yuboring.")
    video_file_id = message.video.file_id
    await state.update_data(file_id=video_file_id)
    await message.answer("📝 Endi qo‘shimcha ma’lumot kiriting (janri, tavsifi va h.k.):")
    await state.set_state(AddMovie.waiting_for_description)

@dp.message(AddMovie.waiting_for_description)
async def get_description(message: Message, state: FSMContext):
    description = message.text.strip()
    data = await state.get_data()
    code = data["code"]
    name = data["name"]
    file_id = data["file_id"]

    cursor.execute("INSERT INTO movies (code, name, file_id, description) VALUES (?, ?, ?, ?)",
                   (code, name, file_id, description))
    conn.commit()

    await message.answer(f"✅ Kino saqlandi!\n🎟 Kod: <code>{code}</code>\n🎞 Nomi: {name}")
    await state.clear()

# Mavjud kinolar ro‘yxati
@dp.message(F.text == "🎞 Mavjud kinolar")
async def show_movies(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    cursor.execute("SELECT code, name FROM movies")
    movies = cursor.fetchall()
    if not movies:
        return await message.answer("📭 Hech qanday kino mavjud emas.")
    
    msg = "<b>🎞 Mavjud kinolar:</b>\n\n"
    for code, name in movies:
        msg += f"🎟 <b>Kod:</b> <code>{code}</code>\n🎬 <b>Nomi:</b> {name}\n\n"
    await message.answer(msg)

# Foydalanuvchi kod yuborganda
@dp.message()
async def user_code_handler(message: Message):
    if message.from_user.id == ADMIN_ID:
        return
    code = message.text.strip()
    cursor.execute("SELECT name, file_id, description FROM movies WHERE code = ?", (code,))
    result = cursor.fetchone()
    if result:
        name, file_id, description = result
        await message.answer_video(file_id, caption=f"<b>🎞Film nomi</b>👉 {name} 👈\n\n<b>📽Film haqida malumot </b> \n{description}")
    else:
        await message.answer("❌ Bunday kod topilmadi.")

# Botni ishga tushurish
async def main():
    logger.info("✅ BOT ISHGA TUSHDI...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
