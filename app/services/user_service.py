from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional
import logging
from datetime import datetime

from app.models.schema import User, UserProfile, Subscription, ContentHistory, SubscriptionStatus
from app.core.config import settings

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def get_or_create_user(self, telegram_id: int, **kwargs) -> User:
        """Get existing user or create new one"""
        # Check if user exists
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            # Update last activity
            user.last_activity = datetime.now()
            await self.db.commit()
            return user
        
        # Create new user
        user = User(telegram_id=telegram_id, **kwargs)
        self.db.add(user)
        await self.db.flush()  # Get user.id
        
        # Create user profile
        profile = UserProfile(user_id=user.id)
        self.db.add(profile)
        
        # Create trial subscription
        subscription = Subscription.create_trial(user.id, settings.TRIAL_DAYS)
        self.db.add(subscription)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_user_with_relations(self, telegram_id: int) -> Optional[User]:
        """Get user with profile and subscription"""
        stmt = (
            select(User)
            .where(User.telegram_id == telegram_id)
            .options(
                # selectinload(User.profile),
                # selectinload(User.subscription)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_user_profile(
        self,
        user_id: int,
        **profile_data
    ) -> bool:
        """Update user profile"""
        try:
            stmt = (
                update(UserProfile)
                .where(UserProfile.user_id == user_id)
                .values(**profile_data)
            )
            await self.db.execute(stmt)
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating user profile {user_id}: {e}")
            await self.db.rollback()
            return False
    
    async def get_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get user profile"""
        stmt = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get user subscription"""
        stmt = select(Subscription).where(Subscription.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def is_user_subscribed(self, user_id: int) -> bool:
        """Check if user has active subscription"""
        subscription = await self.get_user_subscription(user_id)
        return subscription.is_active if subscription else False
    
    async def save_content_history(
        self,
        user_id: int,
        content_type: str,
        prompt: str,
        generated_content: str
    ) -> bool:
        """Save generated content to history"""
        try:
            history = ContentHistory(
                user_id=user_id,
                content_type=content_type,
                prompt=prompt,
                generated_content=generated_content
            )
            self.db.add(history)
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving content history for user {user_id}: {e}")
            await self.db.rollback()
            return False
    
    async def extend_subscription(
        self,
        user_id: int,
        payment_amount: int,
        payment_reference: str,
        months: int = 1
    ) -> bool:
        """Extend user subscription"""
        try:
            from datetime import timedelta
            
            subscription = await self.get_user_subscription(user_id)
            if not subscription:
                return False
            
            # Extend from current expiry or now, whichever is later
            extend_from = max(subscription.expires_at, datetime.now())
            new_expiry = extend_from + timedelta(days=30 * months)
            
            subscription.expires_at = new_expiry
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.payment_amount = payment_amount
            subscription.payment_reference = payment_reference
            subscription.updated_at = datetime.now()
            
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error extending subscription for user {user_id}: {e}")
            await self.db.rollback()
            return False
    
    async def get_user_content_count(self, user_id: int, days: int = 30) -> int:
        """Get user's content generation count in last N days"""
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        stmt = select(ContentHistory).where(
            ContentHistory.user_id == user_id,
            ContentHistory.created_at >= cutoff_date
        )
        result = await self.db.execute(stmt)
        return len(result.scalars().all())