import asyncio
import logging

from app.bot_core import bot, dp
from app import handlers_user, handlers_admin


async def main():
    logging.basicConfig(level=logging.INFO)
    # На всякий случай — убираем вебхук и старые апдейты
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

