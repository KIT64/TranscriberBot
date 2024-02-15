import asyncio
from aiogram import Bot, Dispatcher

from os import getenv

import handlers


async def main():
    bot = Bot(getenv('BOT_TOKEN'))
    dp = Dispatcher()
    
    dp.include_router(handlers.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    print('Bot has been launched')
    asyncio.run(main())
