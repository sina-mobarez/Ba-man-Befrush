import logging
import sys
from typing import Optional

def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None
) -> None:
    """Setup logging configuration"""
    
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
    
    logging.basicConfig(
        level=getattr(logging, level),
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("bot.log", encoding="utf-8")
        ]
    )
    
    # Set specific loggers
    logging.getLogger("aiogram").setLevel(logging.INFO)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)