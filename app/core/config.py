from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional
import logging


class Settings(BaseSettings):
    # Bot settings
    BOT_TOKEN: str
    OPENROUTER_API_KEY: str
    ADMIN_USER_ID: int

    # Database
    DATABASE_URL: str

    # Redis (optional)
    REDIS_URL: Optional[str] = None

    # Webhook settings
    WEBHOOK_HOST: Optional[str] = None
    WEBHOOK_PATH: str = "/webhook"

    # App settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    TRIAL_DAYS: int = 30

    # Payment settings
    ZARINPAL_MERCHANT_ID: Optional[str] = None

    # Speech-to-text settings
    WHISPER_MODEL_NAME: str = "vhdm/whisper-large-fa-v1"
    AUDIO_MAX_FILE_SIZE_MB: int = 20
    AUDIO_MAX_DURATION_SECONDS: int = 300  # 5 minutes
    AUDIO_CACHE_DIR: Optional[str] = None

    @field_validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        level = v.upper()
        if level not in valid_levels:
            raise ValueError(f'Log level must be one of {valid_levels}')
        return level

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Set global logging config
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
