from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta, timezone
from enum import Enum
from core.db import Base
import secrets
import string

class PageStyle(str, Enum):
    SERIOUS = "جدی"
    FRIENDLY = "دوستانه"
    LUXURY = "لوکس"
    TRADITIONAL = "سنتی"

class AudienceType(str, Enum):
    YOUTH = "جوانان"
    LUXURY = "لاکچری"
    BRIDES = "عروس‌ها"
    GENERAL = "عمومی"

class SalesGoal(str, Enum):
    INCREASE_SALES = "افزایش فروش"
    BRAND_AWARENESS = "آگاهی از برند"
    ENGAGEMENT = "تعامل بیشتر"

class SubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    EXPIRED = "expired"

class ContentType(str, Enum):
    CAPTION = "caption"
    REELS = "reels"
    VISUAL = "visual"
    CALENDAR = "calendar"

class OnboardingStep(str, Enum):
    START = "start"
    NAME = "name"
    PHONE = "phone"
    EMAIL = "email"
    GALLERY_NAME = "gallery_name"
    INSTAGRAM = "instagram"
    TELEGRAM = "telegram"
    CUSTOMERS = "customers"
    CONSTRAINTS = "constraints"
    HELP = "help"
    PHYSICAL_STORE = "physical_store"
    ADDITIONAL_INFO = "additional_info"
    SUMMARY_CONFIRM = "summary_confirm"
    COMPLETED = "completed"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    language_code = Column(String(10), default="fa")
    
    # New fields for onboarding
    display_name = Column(String(100), nullable=True)  # What to call them
    onboarding_step = Column(SQLEnum(OnboardingStep), default=OnboardingStep.START)
    onboarding_completed = Column(Boolean, default=False)
    
    # Referral system
    referral_code = Column(String(10), unique=True, nullable=True)
    referred_by_code = Column(String(10), nullable=True)
    referral_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_activity = Column(DateTime(timezone=True), default=func.now())
    
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    content_history = relationship("ContentHistory", back_populates="user", cascade="all, delete-orphan")
    prompts_used = relationship("PromptHistory", back_populates="user", cascade="all, delete-orphan")
    
    def generate_referral_code(self):
        """Generate unique referral code"""
        if not self.referral_code:
            self.referral_code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Basic business info
    gallery_name = Column(String(200), nullable=True)
    instagram_handle = Column(String(100), nullable=True)
    telegram_channel = Column(String(100), nullable=True)
    
    # Customer analysis
    main_customers = Column(Text, nullable=True)  # Description of main customers
    constraints_and_guidelines = Column(Text, nullable=True)  # Dos and don'ts
    content_help = Column(Text, nullable=True)  # Who helps with content
    has_physical_store = Column(Boolean, nullable=True)
    additional_info = Column(Text, nullable=True)
    
    # AI analysis
    situation_summary = Column(Text, nullable=True)  # AI generated summary
    summary_approved = Column(Boolean, default=False)
    
    # Old fields (keeping for compatibility)
    page_style = Column(SQLEnum(PageStyle), nullable=True)
    audience_type = Column(SQLEnum(AudienceType), nullable=True)
    sales_goal = Column(SQLEnum(SalesGoal), nullable=True)
    business_name = Column(String(200), nullable=True)
    business_description = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.TRIAL)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    payment_amount = Column(Integer, default=0)  # In tomans
    payment_reference = Column(String(100), nullable=True)
    discount_applied = Column(Float, default=0.0)  # Discount percentage
    discount_code = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="subscription")
    
    @classmethod
    def create_trial(cls, user_id: int, trial_days: int = 3):  # Changed to 3 days for new flow
        return cls(
            user_id=user_id,
            status=SubscriptionStatus.TRIAL,
            expires_at=datetime.now(timezone.utc) + timedelta(days=trial_days)
        )
    
    @property
    def is_active(self) -> bool:
        return self.expires_at > datetime.now(timezone.utc) and self.status in [SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE]

class ContentHistory(Base):
    __tablename__ = "content_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    content_type = Column(SQLEnum(ContentType), nullable=False)
    prompt = Column(Text, nullable=False)
    generated_content = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="content_history")

class PromptHistory(Base):
    """Track which prompts are used for content generation"""
    __tablename__ = "prompt_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    prompt_name = Column(String(100), nullable=False)  # e.g. "viral_reels_analysis"
    prompt_content = Column(Text, nullable=False)
    usage_count = Column(Integer, default=1)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="prompts_used")

class DiscountCode(Base):
    """Discount codes for subscriptions"""
    __tablename__ = "discount_codes"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    discount_percentage = Column(Float, nullable=False)  # 0.1 = 10%
    max_uses = Column(Integer, default=100)
    current_uses = Column(Integer, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    @property
    def is_valid(self) -> bool:
        if not self.is_active:
            return False
        if self.current_uses >= self.max_uses:
            return False
        if self.expires_at and self.expires_at < datetime.now(timezone.utc):
            return False
        return True