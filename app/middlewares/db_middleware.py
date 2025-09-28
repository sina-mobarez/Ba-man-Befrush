from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from services.user_service import UserService

class DbSessionMiddleware(BaseMiddleware):
    """
    Middleware to provide each handler with a database session and a UserService instance.
    """
    def __init__(self, session_pool: async_sessionmaker[AsyncSession]):
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Executes the middleware.

        This method is called for every update. It creates a new session,
        initializes the UserService with that session, and passes both to the handler.
        The session is automatically closed when the 'async with' block is exited.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"DbSessionMiddleware called for event type: {type(event).__name__}")
        
        async with self.session_pool() as session:
            # Provide the session object to the handler's data
            data["session"] = session
            # Provide a UserService instance initialized with the current session
            data["user_service"] = UserService(session)
            
            logger.info(f"UserService created and added to data for event: {type(event).__name__}")
            
            # Call the next handler in the chain
            return await handler(event, data)