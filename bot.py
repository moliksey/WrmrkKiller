import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

BOT_TOKEN = "8529603329:AAGD4eHDN1AI-1WnCib3NGR-VeETsKS2UJU"
# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Объект бота
bot = Bot(token=BOT_TOKEN)
# Диспетчер
dp = Dispatcher()

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я эхо-бот. Отправь мне любое сообщение, и я его повторю.")

# Хэндлер на остальные текстовые сообщения
@dp.message(Command("repeat"))
async def echo_handler(message: types.Message):
    await message.answer(f"Я получил твое сообщение: {message.text}")

@dp.message(Command("rm_wrm"))
async def remover_handler(message: types.Message):
    await message.answer(f"Удаляем вотермарку с изображения... (пока не реализовано)")
# Запуск процесса поллинга новых апдейтов
async def main():
    # Удаляем вебхук и пропускаем накопившиеся входящие сообщения
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())