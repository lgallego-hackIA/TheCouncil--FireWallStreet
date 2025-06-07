"""
Logging configuration for theCouncil API system.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

from src.shared.config import settings


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Optional log level to override settings
    """
    level = log_level or settings.LOG_LEVEL
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicate logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_format = logging.Formatter(settings.LOG_FORMAT)
    console_handler.setFormatter(console_format)
    
    # Create file handler
    file_handler = RotatingFileHandler(
        filename=os.path.join(log_dir, "thecouncil.log"),
        maxBytes=10485760,  # 10MB
        backupCount=10,
    )
    file_handler.setLevel(numeric_level)
    file_format = logging.Formatter(settings.LOG_FORMAT)
    file_handler.setFormatter(file_format)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Set levels for third-party loggers to reduce noise
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    
    # Log startup information
    logging.info(f"Logging configured at level: {level}")
