from aiogram import Router, types, F

from core import transcribe_core

router = Router()

@router.message(F.voice)
async def transcribe_audio_message(message: types.Message):
    await message.answer(
        'Аудиосообщение получено, сейчас выдам транскрипцию 😇\n'
        'Подождите, пожалуйста, это может занять некоторое время ⏳'
    )    
    print("Got a message with audio")
    await transcribe_core.transcribe_audio_and_send_to_user(message)