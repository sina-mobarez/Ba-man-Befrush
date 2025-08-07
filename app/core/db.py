from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

class Database:
    def __init__(self, url: str):
        self.engine = create_async_engine(
            url,
            echo=False,
            pool_size=20,
            max_overflow=0,
            pool_pre_ping=True,
            pool_recycle=300,
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def create_tables(self):
        """Create all tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        async with self.session_factory() as session:
            try:
                yield session
            except Exception as e:
                logger.error(f"Database session error: {e}")
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self):
        """Close database connection"""
        await self.engine.dispose()