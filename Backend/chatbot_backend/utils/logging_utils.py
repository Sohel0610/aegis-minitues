"""
Logging Utilities Module
Provides standardized logging functionality across the application
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

# Configure logging
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Set up logging configuration for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("aegis_chatbot")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Prevent adding multiple handlers if function is called multiple times
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log_file is specified
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Global logger instance
logger = setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file=os.getenv("LOG_FILE", "logs/aegis_chatbot.log")
)

def log_agent_action(agent_name: str, action: str, details: Optional[Dict[str, Any]] = None):
    """
    Log agent actions with structured information
    
    Args:
        agent_name: Name of the agent performing the action
        action: Description of the action
        details: Optional dictionary with additional details
    """
    log_message = f"Agent '{agent_name}' - Action: {action}"
    if details:
        log_message += f" - Details: {details}"
    
    logger.info(log_message)

def log_database_operation(database: str, operation: str, details: Optional[Dict[str, Any]] = None):
    """
    Log database operations with structured information
    
    Args:
        database: Database name
        operation: Type of operation
        details: Optional dictionary with additional details
    """
    log_message = f"Database '{database}' - Operation: {operation}"
    if details:
        log_message += f" - Details: {details}"
    
    logger.info(log_message)

def log_error(component: str, error: Exception, details: Optional[Dict[str, Any]] = None):
    """
    Log errors with structured information
    
    Args:
        component: Component where error occurred
        error: Exception object
        details: Optional dictionary with additional details
    """
    log_message = f"Error in '{component}': {str(error)}"
    if details:
        log_message += f" - Details: {details}"
    
    logger.error(log_message, exc_info=True)

def log_warning(component: str, warning: str, details: Optional[Dict[str, Any]] = None):
    """
    Log warnings with structured information
    
    Args:
        component: Component where warning occurred
        warning: Warning message
        details: Optional dictionary with additional details
    """
    log_message = f"Warning in '{component}': {warning}"
    if details:
        log_message += f" - Details: {details}"
    
    logger.warning(log_message)

def log_performance_metric(metric_name: str, value: float, unit: str = "", details: Optional[Dict[str, Any]] = None):
    """
    Log performance metrics
    
    Args:
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement
        details: Optional dictionary with additional details
    """
    log_message = f"Performance Metric - {metric_name}: {value}{unit}"
    if details:
        log_message += f" - Details: {details}"
    
    logger.info(log_message)

# Context manager for timing operations
from contextlib import contextmanager
import time

@contextmanager
def timed_operation(operation_name: str, details: Optional[Dict[str, Any]] = None):
    """
    Context manager to time operations and log performance
    
    Args:
        operation_name: Name of the operation being timed
        details: Optional dictionary with additional details
    """
    start_time = time.time()
    try:
        yield
    finally:
        end_time = time.time()
        duration = end_time - start_time
        log_performance_metric(
            metric_name=operation_name,
            value=duration,
            unit="s",
            details=details
        )

# Export the main logger and utility functions
__all__ = [
    "logger",
    "setup_logging",
    "log_agent_action",
    "log_database_operation",
    "log_error",
    "log_warning",
    "log_performance_metric",
    "timed_operation"
]