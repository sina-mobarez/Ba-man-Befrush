from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional
import logging
from datetime import datetime, timezone

from models.schema import (
    User, UserProfile, Subscription, ContentHistory, SubscriptionStatus,
    OnboardingStep, PromptHistory, DiscountCode
)
from core.config import settings

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
            user.last_activity = datetime.now(timezone.utc)
            await self.db.commit()
            return user
        
        # Create new user
        user = User(telegram_id=telegram_id, **kwargs)
        user.generate_referral_code()
        self.db.add(user)
        await self.db.flush()  # Get user.id
        
        # Create user profile
        profile = UserProfile(user_id=user.id)
        self.db.add(profile)
        
        # Create trial subscription
        subscription = Subscription.create_trial(user.id, settings.TRIAL_DAYS)
        self.db.add(subscription)

        # Handle referral code if provided
        referred_by_code = getattr(user, "referred_by_code", None)
        if referred_by_code:
            ref_stmt = select(User).where(User.referral_code == referred_by_code)
            ref_res = await self.db.execute(ref_stmt)
            ref_user = ref_res.scalar_one_or_none()
            if ref_user:
                ref_user.referral_count = (ref_user.referral_count or 0) + 1
        
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

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by telegram id"""
        stmt = select(User).where(User.telegram_id == telegram_id)
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

    async def update_profile_summary_and_complete(self, user_id: int, summary: str, approved: bool) -> bool:
        """Save summary and optionally mark onboarding completed"""
        try:
            logger.info(f"Starting to update profile summary for user {user_id}")
            logger.info(f"Database session type: {type(self.db)}")
            logger.info(f"Database session state: {self.db.is_active if hasattr(self.db, 'is_active') else 'Unknown'}")
            
            # Save summary
            stmt = (
                update(UserProfile)
                .where(UserProfile.user_id == user_id)
                .values({
                    UserProfile.situation_summary: summary,
                    UserProfile.summary_approved: approved
                })
            )
            logger.info("Executing profile update statement...")
            await self.db.execute(stmt)
            
            # Mark user onboarding completed
            if approved:
                logger.info("Marking user onboarding as completed...")
                user_stmt = (
                    update(User)
                    .where(User.id == user_id)
                    .values(onboarding_completed=True)
                )
                await self.db.execute(user_stmt)
            
            logger.info("Committing changes...")
            await self.db.commit()
            logger.info("Profile summary update completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving profile summary for user {user_id}: {e}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error details: {str(e)}")
            try:
                await self.db.rollback()
            except Exception as rollback_error:
                logger.error(f"Error during rollback: {rollback_error}")
            return False

    async def approved_profile_summary(self, user_id: int, approved: bool) -> bool:
        """Approved summary and optionally mark onboarding completed"""
        try:
            logger.info(f"Starting to update profile summary for user {user_id}")
            logger.info(f"Database session type: {type(self.db)}")
            logger.info(f"Database session state: {self.db.is_active if hasattr(self.db, 'is_active') else 'Unknown'}")
            
            # approved summary
            stmt = (
                update(UserProfile)
                .where(UserProfile.user_id == user_id)
                .values({
                    UserProfile.summary_approved: approved
                })
            )
            logger.info("Executing profile update statement...")
            await self.db.execute(stmt)
            
            # Mark user onboarding completed
            if approved:
                logger.info("Marking user onboarding as completed...")
                user_stmt = (
                    update(User)
                    .where(User.id == user_id)
                    .values(onboarding_completed=True)
                )
                await self.db.execute(user_stmt)
            
            logger.info("Committing changes...")
            await self.db.commit()
            logger.info("Profile summary update completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error saving profile summary for user {user_id}: {e}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error details: {str(e)}")
            try:
                await self.db.rollback()
            except Exception as rollback_error:
                logger.error(f"Error during rollback: {rollback_error}")
            return False

    async def update_onboarding_step(self, user_id: int, step: OnboardingStep) -> bool:
        """Update user's onboarding step"""
        try:
            stmt = (
                update(User)
                .where(User.id == user_id)
                .values(onboarding_step=step)
            )
            await self.db.execute(stmt)
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating onboarding step for user {user_id}: {e}")
            await self.db.rollback()
            return False

    async def update_user_display_name(self, user_id: int, display_name: str) -> bool:
        try:
            stmt = update(User).where(User.id == user_id).values(display_name=display_name)
            await self.db.execute(stmt)
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating display name for user {user_id}: {e}")
            await self.db.rollback()
            return False

    async def update_user_phone(self, user_id: int, phone: str) -> bool:
        try:
            stmt = update(User).where(User.id == user_id).values(phone=phone)
            await self.db.execute(stmt)
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating phone for user {user_id}: {e}")
            await self.db.rollback()
            return False

    async def update_user_email(self, user_id: int, email: str) -> bool:
        try:
            stmt = update(User).where(User.id == user_id).values(email=email)
            await self.db.execute(stmt)
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating email for user {user_id}: {e}")
            await self.db.rollback()
            return False

    async def update_gallery_name(self, user_id: int, gallery_name: str) -> bool:
        return await self.update_user_profile(user_id, gallery_name=gallery_name)

    async def update_instagram_handle(self, user_id: int, instagram: str) -> bool:
        return await self.update_user_profile(user_id, instagram_handle=instagram)

    async def update_telegram_channel(self, user_id: int, telegram: str) -> bool:
        return await self.update_user_profile(user_id, telegram_channel=telegram)

    async def update_main_customers(self, user_id: int, customers: str) -> bool:
        return await self.update_user_profile(user_id, main_customers=customers)

    async def update_constraints(self, user_id: int, constraints: str) -> bool:
        return await self.update_user_profile(user_id, constraints_and_guidelines=constraints)

    async def update_content_help(self, user_id: int, help_info: str) -> bool:
        return await self.update_user_profile(user_id, content_help=help_info)

    async def update_physical_store(self, user_id: int, has_store: bool) -> bool:
        return await self.update_user_profile(user_id, has_physical_store=has_store)

    async def update_additional_info(self, user_id: int, info: str) -> bool:
        return await self.update_user_profile(user_id, additional_info=info)
    
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

    async def save_prompt_usage(
        self,
        user_id: int,
        prompt_name: str,
        prompt_content: str
    ) -> bool:
        """Insert or increment prompt usage for analytics"""
        try:
            stmt = select(PromptHistory).where(
                PromptHistory.user_id == user_id,
                PromptHistory.prompt_name == prompt_name
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                existing.usage_count += 1
                existing.prompt_content = prompt_content
            else:
                self.db.add(PromptHistory(
                    user_id=user_id,
                    prompt_name=prompt_name,
                    prompt_content=prompt_content,
                    usage_count=1
                ))
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving prompt usage for user {user_id}: {e}")
            await self.db.rollback()
            return False

    async def apply_discount_code(self, code: str, user_id: int) -> Optional[DiscountCode]:
        """Validate and mark discount usage if valid"""
        try:
            stmt = select(DiscountCode).where(DiscountCode.code == code)
            result = await self.db.execute(stmt)
            discount = result.scalar_one_or_none()
            if not discount or not discount.is_valid:
                return None
            discount.current_uses += 1
            await self.db.commit()
            return discount
        except Exception as e:
            logger.error(f"Error applying discount code '{code}' for user {user_id}: {e}")
            await self.db.rollback()
            return None
    
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
            extend_from = max(subscription.expires_at, datetime.now(timezone.utc))
            new_expiry = extend_from + timedelta(days=30 * months)
            
            subscription.expires_at = new_expiry
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.payment_amount = payment_amount
            subscription.payment_reference = payment_reference
            subscription.updated_at = datetime.now(timezone.utc)
            
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error extending subscription for user {user_id}: {e}")
            await self.db.rollback()
            return False

    async def update_subscription_discount(self, user_id: int, code: DiscountCode) -> bool:
        """Attach discount to user's subscription"""
        try:
            subscription = await self.get_user_subscription(user_id)
            if not subscription:
                return False
            subscription.discount_applied = code.discount_percentage
            subscription.discount_code = code.code
            subscription.updated_at = datetime.now(timezone.utc)
            await self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating subscription discount for user {user_id}: {e}")
            await self.db.rollback()
            return False

    async def ensure_referral_code(self, user_id: int) -> Optional[str]:
        """Ensure user has a referral code and return it"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return None
        if not user.referral_code:
            user.generate_referral_code()
            await self.db.commit()
        return user.referral_code
    
    async def get_user_content_count(self, user_id: int, days: int = 30) -> int:
        """Get user's content generation count in last N days"""
        from datetime import timedelta
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = select(ContentHistory).where(
            ContentHistory.user_id == user_id,
            ContentHistory.created_at >= cutoff_date
        )
        result = await self.db.execute(stmt)
        return len(result.scalars().all())