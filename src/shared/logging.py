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
    
    # Detect environment (serverless or local)
    is_serverless = os.environ.get('VERCEL') == '1' or os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None
    
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
    
    # Only create file handler if not in serverless environment
    file_handler = None
    if not is_serverless:
        try:
            # Create logs directory if it doesn't exist
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            
            # Create file handler
            file_handler = RotatingFileHandler(
                filename=os.path.join(log_dir, "thecouncil.log"),
                maxBytes=10485760,  # 10MB
                backupCount=10,
            )
            file_handler.setLevel(numeric_level)
            file_format = logging.Formatter(settings.LOG_FORMAT)
            file_handler.setFormatter(file_format)
        except (OSError, IOError) as e:
            # If we can't create log file, just continue with console logging
            print(f"Warning: Could not set up file logging: {str(e)}")
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    if file_handler is not None:
        root_logger.addHandler(file_handler)
    
    # Log configuration
    logging.info(f"Logging configured at level: {level}")
    if is_serverless:
        logging.info("Running in serverless environment, file logging disabled.")
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    
    # Log startup information
    logging.info(f"Logging configured at level: {level}")
