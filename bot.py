import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery
from aiogram.types import BufferedInputFile
import torch
from PIL import Image
from watermark_remover import WatermarkRemover
import io
from picture_processing import process_large_image, process_test_image

BOT_TOKEN = "8529603329:AAGD4eHDN1AI-1WnCib3NGR-VeETsKS2UJU"
# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

# Объект бота
bot = Bot(token=BOT_TOKEN)
# Диспетчер
dp = Dispatcher()
class WatermarkRemoval(StatesGroup):
    waiting_for_photo = State()
    waiting_for_fullres_choice = State()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load the trained model
model = WatermarkRemover().to(device)
model_path = "model.pth"  # Replace with the path to your saved model
model.load_state_dict(torch.load(model_path, map_location=device))
model.eval()

fullres_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="⚡ Да (полное качество)", callback_data="fullres_yes"),
            InlineKeyboardButton(text="❌ Нет", callback_data="fullres_no")
        ]
    ]
)

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🧹 Удалить водяной знак")]
    ],
    resize_keyboard=True
)

cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Отменить")]
    ],
    resize_keyboard=True
)

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот для удаления водяных знаков.\n"
        "Нажми кнопку ниже, чтобы начать.",
        reply_markup=main_keyboard
    )

@dp.message(Command("rm_wrm"))
@dp.message(lambda message: message.text == "🧹 Удалить водяной знак")
async def remover_handler(message: types.Message, state: FSMContext):
    await state.set_state(WatermarkRemoval.waiting_for_photo)
    await message.answer(
        "Отправьте фото, с которого нужно удалить водяной знак.",
        reply_markup=cancel_keyboard
    )

# Команда для отмены
@dp.message(WatermarkRemoval.waiting_for_photo, lambda message: message.text == "❌ Отменить")
@dp.message(WatermarkRemoval.waiting_for_photo, Command("cancel"))
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активной операции")
        return
    
    await state.clear()
    await message.answer(
        "❌ Операция отменена",
        reply_markup=main_keyboard
    )

@dp.message(WatermarkRemoval.waiting_for_photo, lambda message: message.photo or message.document)
async def photo_handler(message: Message, state: FSMContext):

    if message.photo:
        photo = message.photo[-1]
    else:
        photo = message.document

    file_info = await bot.get_file(photo.file_id)
    file_path = file_info.file_path

    downloaded_file = await bot.download_file(file_path)

    image_bytes = io.BytesIO(downloaded_file.read())
    watermarked_image = Image.open(image_bytes).convert("RGB")

    await state.update_data(image=image_bytes.getvalue())

    await message.answer("⚡ Делаю быстрый тестовый результат...")

    predicted_pil = process_test_image(watermarked_image, model, device)

    output_buffer = io.BytesIO()
    predicted_pil.save(output_buffer, format="PNG")
    output_buffer.seek(0)

    await message.answer_photo(
        BufferedInputFile(output_buffer.getvalue(), filename="preview.png"),
        caption="Предварительный результат."
    )

    await state.set_state(WatermarkRemoval.waiting_for_fullres_choice)

    await message.answer(
        "Сделать обработку в полном разрешении?",
        reply_markup=fullres_keyboard
    )

@dp.message(WatermarkRemoval.waiting_for_photo)
async def wrong_input_handler(message: types.Message, state: FSMContext):
    await message.answer(
        "Пожалуйста, отправьте именно фото!\n"
        "Если хотите отменить операцию, отправьте /cancel",
        reply_markup=cancel_keyboard
    )

@dp.callback_query(WatermarkRemoval.waiting_for_fullres_choice, lambda c: c.data == "fullres_yes")
async def process_full_resolution(callback: CallbackQuery, state: FSMContext):

    await callback.message.answer("🧠 Обрабатываю изображение в полном разрешении...")

    data = await state.get_data()
    image_bytes = io.BytesIO(data["image"])

    watermarked_image = Image.open(image_bytes).convert("RGB")

    result = process_large_image(watermarked_image, model, device=device)

    output_buffer = io.BytesIO()
    result.save(output_buffer, format="PNG")
    output_buffer.seek(0)

    await callback.message.answer_photo(
        BufferedInputFile(output_buffer.getvalue(), filename="preview.png"),
        caption="✅ Готово (полное качество)"
    )

    await state.clear()

    await callback.message.answer(
        "Можете начать удаление вотермарки с нового фото.",
        reply_markup=main_keyboard
    )

@dp.callback_query(WatermarkRemoval.waiting_for_fullres_choice, lambda c: c.data == "fullres_no")
async def skip_full_resolution(callback: CallbackQuery, state: FSMContext):

    await callback.message.answer(
        "Хорошо 👍 Используйте бота снова, если нужно обработать другое фото.",
        reply_markup=main_keyboard
    )

    await state.clear()

async def main():
    # Удаляем вебхук и пропускаем накопившиеся входящие сообщения
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())