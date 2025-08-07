import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from contextlib import asynccontextmanager

from core.config import settings
from core.logging_setup import setup_logging
from core.db import Database
from handlers.common import register_handlers

# Setup logging
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Global database instance
db: Database = None

@asynccontextmanager
async def lifespan():
    """Application lifespan manager"""
    global db
    
    # Startup
    logger.info("Starting AI Jewelry Bot...")
    
    # Initialize database
    db = Database(settings.DATABASE_URL)
    await db.create_tables()
    logger.info("Database initialized")
    
    try:
        yield
    finally:
        # Cleanup
        if db:
            await db.close()
        logger.info("Bot stopped")

async def main():
    """Main function to run the bot"""
    
    # Create bot and dispatcher
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    
    # Register handlers
    router = register_handlers()
    dp.include_router(router)
    
    # Use lifespan manager
    async with lifespan():
        
        # Start bot
        if settings.WEBHOOK_HOST:
            # Webhook mode
            logger.info(f"Starting bot with webhook: {settings.WEBHOOK_HOST}{settings.WEBHOOK_PATH}")
            await dp.start_polling(bot, skip_updates=True)
        else:
            # Polling mode
            logger.info("Starting bot with polling...")
            await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())