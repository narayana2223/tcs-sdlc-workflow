"""
Logging configuration for the analysis engine.
Provides structured logging with proper formatting and multiple output options.
"""

import logging
import logging.config
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'ENDC': '\033[0m'       # End color
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['ENDC'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['ENDC']}"
        return super().format(record)


class AnalysisLogFilter(logging.Filter):
    """Custom filter to add analysis context to log records."""
    
    def __init__(self):
        super().__init__()
        self.analysis_context = {}
    
    def filter(self, record):
        # Add analysis context to the record
        for key, value in self.analysis_context.items():
            setattr(record, key, value)
        return True
    
    def set_context(self, **kwargs):
        """Set analysis context for logging."""
        self.analysis_context.update(kwargs)
    
    def clear_context(self):
        """Clear analysis context."""
        self.analysis_context.clear()


# Global filter instance
analysis_filter = AnalysisLogFilter()


def setup_logging(
    level: str = 'INFO',
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_colors: bool = True,
    log_format: Optional[str] = None
) -> None:
    """
    Set up logging configuration for the analysis engine.
    
    Args:
        level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_file: Optional log file path
        enable_console: Whether to enable console logging
        enable_colors: Whether to enable colored console output
        log_format: Custom log format string
    """
    
    # Default log format
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Detailed format for file logging
    detailed_format = (
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - '
        '%(funcName)s() - %(message)s'
    )
    
    # Create formatters
    console_formatter = ColoredFormatter(log_format) if enable_colors else logging.Formatter(log_format)
    file_formatter = logging.Formatter(detailed_format)
    
    # Clear existing handlers
    logging.root.handlers.clear()
    
    # Configure root logger
    logging.root.setLevel(level)
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(analysis_filter)
        logging.root.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel('DEBUG')  # Always log debug to file
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(analysis_filter)
        logging.root.addHandler(file_handler)
    
    # Set specific logger levels
    _configure_third_party_loggers()
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {level}, Console: {enable_console}, File: {log_file}")


def setup_analysis_logging(
    analysis_id: str,
    repo_url: str,
    log_dir: str = "logs"
) -> str:
    """
    Set up logging for a specific analysis session.
    
    Args:
        analysis_id: Unique identifier for the analysis
        repo_url: Repository URL being analyzed
        log_dir: Directory for log files
        
    Returns:
        Path to the created log file
    """
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_repo_name = _sanitize_filename(repo_url.split('/')[-1] if '/' in repo_url else repo_url)
    log_filename = f"analysis_{safe_repo_name}_{timestamp}.log"
    log_file = os.path.join(log_dir, log_filename)
    
    # Set up logging
    setup_logging(
        level='DEBUG',
        log_file=log_file,
        enable_console=True,
        enable_colors=True
    )
    
    # Set analysis context
    analysis_filter.set_context(
        analysis_id=analysis_id,
        repo_url=repo_url,
        timestamp=timestamp
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Started analysis logging - ID: {analysis_id}, Repo: {repo_url}")
    
    return log_file


def get_logging_config() -> Dict[str, Any]:
    """
    Get comprehensive logging configuration dictionary.
    
    Returns:
        Logging configuration dictionary for use with logging.config.dictConfig
    """
    
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'detailed': {
                'format': (
                    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - '
                    '%(funcName)s() - %(message)s'
                )
            },
            'colored': {
                '()': ColoredFormatter,
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'json': {
                'format': '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s", "file": "%(filename)s", "line": %(lineno)d}'
            }
        },
        'filters': {
            'analysis_context': {
                '()': AnalysisLogFilter
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'colored',
                'filters': ['analysis_context'],
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filters': ['analysis_context'],
                'filename': 'analysis.log',
                'mode': 'a',
                'encoding': 'utf-8'
            },
            'rotating_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filters': ['analysis_context'],
                'filename': 'analysis.log',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
                'encoding': 'utf-8'
            }
        },
        'loggers': {
            'analysis_engine': {
                'level': 'DEBUG',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'git': {
                'level': 'WARNING',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'urllib3': {
                'level': 'WARNING',
                'handlers': ['console'],
                'propagate': False
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console']
        }
    }


def configure_logger_for_module(module_name: str, level: str = 'INFO') -> logging.Logger:
    """
    Configure and return a logger for a specific module.
    
    Args:
        module_name: Name of the module
        level: Logging level for this module
        
    Returns:
        Configured logger instance
    """
    
    logger = logging.getLogger(module_name)
    logger.setLevel(level)
    
    # Add analysis filter if not already present
    if not any(isinstance(f, AnalysisLogFilter) for f in logger.filters):
        logger.addFilter(analysis_filter)
    
    return logger


def set_analysis_context(**kwargs):
    """
    Set analysis context for all loggers.
    
    Args:
        **kwargs: Context key-value pairs
    """
    analysis_filter.set_context(**kwargs)


def clear_analysis_context():
    """Clear analysis context for all loggers."""
    analysis_filter.clear_context()


def _configure_third_party_loggers():
    """Configure third-party library loggers to reduce noise."""
    
    # Git library
    logging.getLogger('git').setLevel(logging.WARNING)
    
    # HTTP libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    # Network libraries
    logging.getLogger('networkx').setLevel(logging.WARNING)


def _sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system operations."""
    
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove .git extension if present
    if filename.endswith('.git'):
        filename = filename[:-4]
    
    # Limit length
    return filename[:50] if len(filename) > 50 else filename


# Performance monitoring decorator
def log_performance(func):
    """Decorator to log function performance."""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"{func.__name__} completed in {duration:.2f} seconds")
            return result
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.error(f"{func.__name__} failed after {duration:.2f} seconds: {e}")
            raise
    
    return wrapper


# Example usage and testing
if __name__ == "__main__":
    # Test the logging configuration
    setup_logging(level='DEBUG', enable_colors=True)
    
    logger = logging.getLogger(__name__)
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test with context
    set_analysis_context(repo_url="https://github.com/test/repo", analysis_id="test-123")
    logger.info("This message has analysis context")
    
    clear_analysis_context()
    logger.info("This message has no context")