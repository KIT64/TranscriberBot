from aiogram import Router, types, F

from core import make_subtitles_core


router = Router()
router.message.filter((F.chat.type == "supergroup") | (F.chat.type == "group"))

@router.message()
async def make_subtitles_input(message: types.Message):
    # if message.attachments:
    #     for attachment in message.attachments:
    #         if attachment.content_type.startswith('video/'):
    if message.video:
        await make_subtitles_core.make_subtitles_and_send_to_user(message)