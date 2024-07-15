from aiogram import Router, types, F

from core import make_subtitles_core


router = Router()
router.message.filter((F.chat.type == "supergroup") | (F.chat.type == "group"))

@router.message(F.video)
async def make_subtitles_input(message: types.Message):
    await message.answer(
        'Видео было получено, сейчас выдам субтитры 😇'
    )
    await make_subtitles_core.make_subtitles_and_send_to_user(message)
