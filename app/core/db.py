import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

class Database:
    """
    Manages the database engine and session factory.
    """
    def __init__(self, url: str):
        """
        Initializes the database engine and session factory with production-ready settings.
        :param url: The database connection URL.
        """
        self.engine = create_async_engine(
            url,
            echo=False,  # Set to True for debugging SQL queries
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=300,  # Recycle connections every 5 minutes
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        logger.info("Database engine and session factory initialized.")

    async def create_tables(self):
        """Creates all database tables defined in the Base metadata."""
        async with self.engine.begin() as conn:
            # Import all models here to ensure their metadata is registered on Base
            from models.schema import User, UserProfile, Subscription, ContentHistory
            
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created or already exist.")

    def get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """
        Returns the configured session factory.
        This is the single entry point for the application (specifically the middleware)
        to get the tool required for creating new sessions.
        """
        return self.session_factory

    async def close(self):
        """Closes the database engine's connection pool."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection pool closed.")