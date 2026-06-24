"""
Logging Configuration
Centralized logging setup for the application
"""

import logging
import logging.config
from pathlib import Path
from app.config import settings


# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO" if not settings.debug else "DEBUG",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "app.log",
            "formatter": "detailed",
            "level": "INFO",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "error.log",
            "formatter": "detailed",
            "level": "ERROR",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 10,
        },
    },
    "loggers": {
        "app": {
            "level": "DEBUG" if settings.debug else "INFO",
            "handlers": ["console", "file", "error_file"],
            "propagate": False,
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
}


def setup_logging():
    """Setup logging configuration"""
    try:
        logging.config.dictConfig(LOGGING_CONFIG)
    except Exception:
        # Fallback to basic configuration if JSON logging not available
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


# Configure logging
setup_logging()

# Get logger for app
logger = logging.getLogger("app")
