from aiogram import Router, types, F
from core import transcribe_core

router = Router()


@router.message(F.voice | F.audio)
async def transcribe_voice_message(message: types.Message):
    try:
        if message.chat.type == 'private':
            await message.answer(
                'Аудиосообщение получено, сейчас выдам транскрипцию 😇\n'
                'Подождите, пожалуйста, это может занять некоторое время ⏳'
            )
        print(f"Got an audio message in {message.chat.type} chat")
        await transcribe_core.transcribe_audio_and_send_to_user(message)
    except Exception as e:
        print(f"Unexpected error in transcribe_voice_message: {e}")
        await message.answer("Произошла неожиданная ошибка при обработке аудиосообщения. Пожалуйста, попробуйте позже.")


@router.channel_post(F.voice | F.audio)
async def transcribe_channel_voice(message: types.Message):
    try:
        print("Got an audio message from a channel")
        await transcribe_core.transcribe_audio_and_send_to_user(message, is_channel=True)
    except Exception as e:
        print(f"Unexpected error in transcribe_channel_voice: {e}")
        await message.answer(
            "Произошла неожиданная ошибка при обработке аудиосообщения в канале. Пожалуйста, попробуйте позже.",
            reply_to_message_id=message.message_id,
        )
