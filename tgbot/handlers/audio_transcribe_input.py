from aiogram import Router, types, F

from core import transcribe_core

router = Router()

@router.message(F.voice)
async def transcribe_voice_message(message: types.Message):
    if message.chat.type == 'private':
        await message.answer(
            'Аудиосообщение получено, сейчас выдам транскрипцию 😇\n'
            'Подождите, пожалуйста, это может занять некоторое время ⏳'
        )
    print(f"Got a voice message in {message.chat.type} chat")
    await transcribe_core.transcribe_audio_and_send_to_user(message)

@router.channel_post(F.voice)
async def transcribe_channel_voice(message: types.Message):
    print("Got a voice message from a channel")
    await transcribe_core.transcribe_audio_and_send_to_user(message, is_channel=True)