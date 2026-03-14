import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

BOT_TOKEN = "8529603329:AAGD4eHDN1AI-1WnCib3NGR-VeETsKS2UJU"
# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Объект бота
bot = Bot(token=BOT_TOKEN)
# Диспетчер
dp = Dispatcher()
class WatermarkRemoval(StatesGroup):
    waiting_for_photo = State()

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я эхо-бот. Отправь мне любое сообщение, и я его повторю.")

@dp.message(Command("rm_wrm"))
async def remover_handler(message: types.Message, state: FSMContext):
    await state.set_state(WatermarkRemoval.waiting_for_photo)
    await message.answer(
        "Отправьте фото, с которого нужно удалить водяной знак.\n"
        "Я буду ждать именно фото, не текст и не другие файлы."
    )

@dp.message(WatermarkRemoval.waiting_for_photo, lambda message: message.photo)
async def photo_handler(message: types.Message, state: FSMContext):
    # Получаем фото (берем самую большую версию - последнюю в списке)
    photo = message.photo[-1]
    
    # Информация о фото
    file_info = await bot.get_file(photo.file_id)
    file_path = file_info.file_path
    
    await message.answer(
        f"✅ Начинаю обработку фото для удаления водяного знака!\n"
        f"Размер: {photo.width}x{photo.height}\n"
        f"File ID: {photo.file_id}\n"
        f"Размер файла: {file_info.file_size} байт\n"
        f"Путь на сервере: {file_path}\n\n"
        f"🔧 Удаление водяного знака... (пока не реализовано)"
    )
    
    # Скачиваем фото для обработки (пример)
    try:
        downloaded_file = await bot.download_file(file_path)
        # Здесь будет ваша логика удаления водяного знака
        # process_image(downloaded_file)
        
        # Пока просто отправляем уведомление
        await message.answer("🖼️ Фото получено и готово к обработке!")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка при скачивании фото: {e}")
    
    # Очищаем состояние, чтобы следующие фото не обрабатывались
    await state.clear()
    await message.answer("Состояние сброшено. Чтобы обработать новое фото, снова используйте /rm_wrm")

@dp.message(WatermarkRemoval.waiting_for_photo)
async def wrong_input_handler(message: types.Message, state: FSMContext):
    await message.answer(
        "Пожалуйста, отправьте именно фото!\n"
        "Если хотите отменить операцию, отправьте /cancel"
    )

# Команда для отмены
@dp.message(WatermarkRemoval.waiting_for_photo, Command("cancel"))
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активной операции")
        return
    
    await state.clear()
    await message.answer("Операция отменена")

async def main():
    # Удаляем вебхук и пропускаем накопившиеся входящие сообщения
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())