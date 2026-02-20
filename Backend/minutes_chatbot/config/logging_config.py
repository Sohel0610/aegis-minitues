"""
Logging Configuration for Minutes Chatbot

Configures structured logging with both console and file handlers.
"""

import logging
import logging.handlers
from pythonjsonlogger import jsonlogger
from minutes_chatbot.config.settings import settings


def setup_logging():
    """Configure logging for the application"""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Console Handler (Human-readable format)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File Handler (JSON format for structured logging)
    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    json_formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)
    
    return logger


# Create logger instance
logger = setup_logging()
