import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from core.config import settings
from core.db import Database
from core.logging_setup import setup_logging
from handlers.common import router as common_router
from middlewares.db_middleware import DbSessionMiddleware
from services.ai_service import AIService
from services.speech_service import SpeechService


setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


async def main() -> None:
    """
    Main function to initialize and run the bot.
    This function sets up the database, services, dispatcher, and starts polling.
    """
    
    # 1. Initialize Database and Session Factory
    logger.info("Initializing database connection...")
    db = Database(url=settings.DATABASE_URL)
    await db.create_tables()
    session_maker: async_sessionmaker[AsyncSession] = db.session_factory

    # 2. Initialize Services (as singletons)
    logger.info("Initializing services...")
    ai_service = AIService()
    speech_service = SpeechService()

    # 3. Initialize Bot and Dispatcher
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # 4. Register Middleware
    # The DbSessionMiddleware is crucial for providing a clean database session to each handler.
    dp.update.middleware(DbSessionMiddleware(session_pool=session_maker))

    # 5. Register Routers
    # All handlers from your 'handlers' package will be included.
    dp.include_router(common_router)

    # 6. Start Polling
    # The 'ai_service' is passed here as a workflow data object, making it available
    # to all handlers and middlewares. The UserService will be created on-the-fly
    # by a middleware that depends on the session from DbSessionMiddleware.
    logger.info("Starting bot with polling...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, ai_service=ai_service, speech_service=speech_service)
    finally:
        # Graceful shutdown
        logger.info("Stopping bot and closing database connection...")
        await bot.session.close()
        await db.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user.")