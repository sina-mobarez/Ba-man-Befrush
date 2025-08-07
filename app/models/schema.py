from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timedelta, timezone
from enum import Enum
from core.db import Base

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

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    language_code = Column(String(10), default="fa")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_activity = Column(DateTime(timezone=True), default=func.now())
    
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    content_history = relationship("ContentHistory", back_populates="user", cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    page_style = Column(SQLEnum(PageStyle), default=PageStyle.FRIENDLY)
    audience_type = Column(SQLEnum(AudienceType), default=AudienceType.GENERAL)
    sales_goal = Column(SQLEnum(SalesGoal), default=SalesGoal.INCREASE_SALES)
    
    business_name = Column(String(200), nullable=True)
    business_description = Column(Text, nullable=True)
    instagram_handle = Column(String(100), nullable=True)
    
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
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="subscription")
    
    @classmethod
    def create_trial(cls, user_id: int, trial_days: int = 30):
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