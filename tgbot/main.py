import asyncio
from aiogram import Bot, Dispatcher

from os import getenv

from handlers import (
    common_handlers,
    transcribe_input,
    fetch_subtitles_input,
    make_subtitles_input,
    audio_transcribe_input
)


async def main():
    bot = Bot(getenv('BOT_TOKEN'))
    dp = Dispatcher()
    
    dp.include_router(common_handlers.router)
    dp.include_router(transcribe_input.router)
    dp.include_router(fetch_subtitles_input.router)
    dp.include_router(make_subtitles_input.router)
    dp.include_router(audio_transcribe_input.router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    print('Bot has been launched')
    asyncio.run(main())
