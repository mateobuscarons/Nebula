"""Logging configuration for the Guided Learning System."""

import logging
import sys
from pathlib import Path
from typing import Optional

from config import system_config


def setup_logging(log_file: Optional[str] = None, log_level: Optional[str] = None):
    """
    Configure logging for the application.

    Args:
        log_file: Path to log file (None for console only)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    log_level = log_level or system_config.log_level
    log_file = log_file or system_config.log_file

    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    root_logger.handlers = []

    # Console handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (DEBUG and above) if log file specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        logging.info(f"Logging to file: {log_file}")

    # Log the configuration
    logging.info("="*60)
    logging.info("Guided Learning System - Logging Initialized")
    logging.info(f"Log Level: {log_level}")
    logging.info(f"Log File: {log_file or 'Console only'}")
    logging.info("="*60)

    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
