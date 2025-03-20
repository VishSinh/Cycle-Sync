# custom_logging.py
import logging
import os
import inspect
import sys
from logging.handlers import RotatingFileHandler
import re

# ANSI color codes for console output
COLORS = {
    'DEBUG': '\033[36m',      # Cyan
    'INFO': '\033[32m',       # Green
    'WARNING': '\033[33m',    # Yellow
    'ERROR': '\033[31m',      # Red
    'CRITICAL': '\033[41m',   # Red background
    'RESET': '\033[0m'        # Reset to default
}

class CustomFormatter(logging.Formatter):
    """
    A formatter that adds file:function:line information to log records.
    """
    def format(self, record):
        # Add the calling function and line number if not already present
        if not hasattr(record, 'func_lineno'):
            # Get caller information
            current_frame = inspect.currentframe()
            caller_frame = inspect.getouterframes(current_frame, 2)
            # Look for the appropriate calling frame (skipping logging internals)
            frame_index = 1
            while frame_index < len(caller_frame):
                if caller_frame[frame_index].filename != __file__ and 'logging' not in caller_frame[frame_index].filename:
                    break
                frame_index += 1
            
            if frame_index < len(caller_frame):
                record.func_lineno = f"{os.path.basename(caller_frame[frame_index].filename)}:{caller_frame[frame_index].function}:{caller_frame[frame_index].lineno}"
            else:
                record.func_lineno = "unknown:unknown:0"
        
        # Call the original formatter
        return super().format(record)

class ColoredConsoleFormatter(CustomFormatter):
    """
    A formatter that adds colors to console output based on log level,
    but only for console output (not files).
    """
    def format(self, record):
        # First get the formatted message with all the custom info
        message = super().format(record)
        
        # Add color if terminal supports it
        levelname = record.levelname
        
        # Check if output is to a terminal that supports colors
        is_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
        
        if is_tty and levelname in COLORS:
            message = COLORS[levelname] + message + COLORS['RESET']
            
        return message

# Global output mode control
# Valid values: 'console', 'file', 'both'
OUTPUT_MODE = 'console'

def set_output_mode(mode):
    """
    Set the global output mode for loggers.
    
    Args:
        mode (str): One of 'console', 'file', or 'both'
    """
    global OUTPUT_MODE
    valid_modes = ('console', 'file', 'both')
    if mode not in valid_modes:
        raise ValueError(f"Invalid output mode: {mode}. Must be one of {valid_modes}")
    
    OUTPUT_MODE = mode
    
    # Update existing handlers if needed
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            handler.setLevel(logging.NOTSET if mode in ('console', 'both') else logging.CRITICAL)
        elif isinstance(handler, logging.FileHandler) and not handler.baseFilename.endswith('error.log'):
            handler.setLevel(logging.NOTSET if mode in ('file', 'both') else logging.CRITICAL)
    
    return OUTPUT_MODE

def get_django_logging_config(log_dir='logs', 
                             console_level='INFO', 
                             file_level='DEBUG',
                             max_file_size_mb=10, 
                             backup_count=5,
                             output_mode='console',
                             colored_console=True):
    """
    Returns a Django logging configuration dictionary.
    
    Args:
        log_dir (str): Directory to store log files
        console_level (str): Logging level for console output
        file_level (str): Logging level for file output
        max_file_size_mb (int): Maximum size of each log file in MB
        backup_count (int): Number of backup files to keep
        output_mode (str): Where to output logs - 'console', 'file', or 'both'
        colored_console (bool): Whether to use colored output in console
    """
    global OUTPUT_MODE
    OUTPUT_MODE = output_mode
    
    # Create log directory if it doesn't exist
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError as e:
            print(f"Error creating log directory: {e}")
            raise

    # Calculate max bytes
    max_bytes = max_file_size_mb * 1024 * 1024

    # Django logging configuration dictionary
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                '()': CustomFormatter,
                'format': '\n%(asctime)s [%(levelname)s] %(name)s - %(func_lineno)s - \n%(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'colored_console': {
                '()': ColoredConsoleFormatter if colored_console else CustomFormatter,
                'format': '\n%(asctime)s [%(levelname)s] %(name)s - %(func_lineno)s - \n%(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'simple': {
                'format': '%(levelname)s %(message)s',
            },
            'django.server': {
                'format': '[%(server_time)s] %(message)s',
            },
        },
        'filters': {
            'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
            },
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse',
            },
        },
        'handlers': {
            'console': {
                'level': console_level if output_mode in ('console', 'both') else 'CRITICAL',
                'class': 'logging.StreamHandler',
                'formatter': 'colored_console',  # Use colored formatter for console
                'stream': sys.stdout,
            },
            'file': {
                'level': file_level if output_mode in ('file', 'both') else 'CRITICAL',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'verbose',  # Use non-colored formatter for files
                'filename': os.path.join(log_dir, 'app.log'),
                'maxBytes': max_bytes,
                'backupCount': backup_count,
            },
            'error_file': {
                'level': 'ERROR',  # Always capture ERROR and CRITICAL
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'verbose',  # Use non-colored formatter for files
                'filename': os.path.join(log_dir, 'error.log'),
                'maxBytes': max_bytes,
                'backupCount': backup_count,
            },
            'django_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'verbose',  # Use non-colored formatter for files
                'filename': os.path.join(log_dir, 'django.log'),
                'maxBytes': max_bytes,
                'backupCount': backup_count,
                'filters': [] if output_mode in ('file', 'both') else ['require_debug_false'],
            },
            'mail_admins': {
                'level': 'ERROR',
                'filters': ['require_debug_false'],
                'class': 'django.utils.log.AdminEmailHandler',
                'formatter': 'verbose',
            },
        },
        'loggers': {
            # Root logger
            '': {
                'handlers': ['console', 'file', 'error_file'],
                'level': 'DEBUG',
                'propagate': True,
            },
            # Django loggers
            'django': {
                'handlers': ['console', 'django_file', 'error_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.server': {
                'handlers': ['console', 'django_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.request': {
                'handlers': ['console', 'django_file', 'mail_admins', 'error_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.db.backends': {
                'handlers': ['console', 'django_file'],
                'level': 'INFO',  # Change to DEBUG to log all SQL queries
                'propagate': False,
            },
            'django.security': {
                'handlers': ['console', 'django_file', 'mail_admins', 'error_file'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }
    
    return logging_config


def create_specialized_logger(name, log_file, level=logging.DEBUG, 
                             max_file_size_mb=5, backup_count=3,
                             colored_console=True,
                             error_log_file=None,
                             respect_global_output_mode=False):
    """
    Create a specialized logger that writes to a specific file.
    
    Args:
        name (str): Logger name
        log_file (str): Path to the log file
        level: Logging level
        max_file_size_mb (int): Maximum size of log file in MB
        backup_count (int): Number of backup files to keep
        colored_console (bool): Whether to use colored output in console
        error_log_file (str): Optional path to error log file. If None, errors 
                            will still go to the main error.log
        respect_global_output_mode (bool): Whether to respect the global OUTPUT_MODE
                                         setting. If False, always logs to file only.
        
    Returns:
        logging.Logger: Specialized logger
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Create formatters
    format_str = '\n%(asctime)s [%(levelname)s] %(name)s - %(func_lineno)s - %(message)s'
    date_fmt = '%Y-%m-%d %H:%M:%S'
    
    # Different formatters for console and file
    # console_formatter = ColoredConsoleFormatter(format_str, datefmt=date_fmt) if colored_console else CustomFormatter(format_str, datefmt=date_fmt)
    file_formatter = CustomFormatter(format_str, datefmt=date_fmt)
    
    # Create the log directory if needed
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Check if handlers already exist (to avoid duplicate handlers)
    file_handler_exists = False
    console_handler_exists = False
    error_handler_exists = False
    
    for handler in logger.handlers:
        if isinstance(handler, RotatingFileHandler):
            if handler.baseFilename == os.path.abspath(log_file):
                file_handler_exists = True
            elif error_log_file and handler.baseFilename == os.path.abspath(error_log_file):
                error_handler_exists = True
        elif isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
            console_handler_exists = True
    
    # Create file handler if doesn't exist
    if not file_handler_exists:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count
        )
        # Ensure file handler is always active
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Create console handler if doesn't exist and if we should log to console
    should_log_to_console = False
    # if not console_handler_exists and should_log_to_console:
    #     console_handler = logging.StreamHandler(sys.stdout)
    #     console_handler.setLevel(level)
    #     console_handler.setFormatter(console_formatter)
    #     logger.addHandler(console_handler)
    
    # Create/use error log file handler
    if error_log_file and not error_handler_exists:
        # Create error log directory if needed
        error_log_dir = os.path.dirname(error_log_file)
        if error_log_dir and not os.path.exists(error_log_dir):
            os.makedirs(error_log_dir)
            
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)  # Only ERROR and CRITICAL
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)
    elif not error_handler_exists:
        # If no specific error log file is provided, use the default error.log
        default_error_log = os.path.join(os.path.dirname(log_file), 'error.log')
        error_handler = RotatingFileHandler(
            default_error_log,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)  # Only ERROR and CRITICAL
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)
    
    return logger


def specialized_logger(name, log_file, level=logging.DEBUG, 
                           max_file_size_mb=5, backup_count=3,
                           error_log_file=None):
    """
    Create a specialized logger that writes ONLY to a specific file,
    completely independent of the global logging configuration.
    
    Args:
        name (str): Logger name (preferably unique to avoid conflicts)
        log_file (str): Path to the log file
        level: Logging level
        max_file_size_mb (int): Maximum size of log file in MB
        backup_count (int): Number of backup files to keep
        error_log_file (str): Optional path to error log file. If None, errors 
                            will still go to the main log file
        
    Returns:
        logging.Logger: File-only specialized logger
    """
    # Create a unique logger name to avoid conflicts with existing loggers
    unique_logger_name = f"file_only.{name}"
    
    # Create logger and explicitly disable propagation to parent loggers
    logger = logging.getLogger(unique_logger_name)
    logger.propagate = False  # This is critical - prevents propagation to root logger
    
    # Reset any existing handlers (in case the function is called multiple times)
    if logger.handlers:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
    
    # Set logger level
    logger.setLevel(level)
    
    # Create formatter
    file_formatter = logging.Formatter(
        '\n%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create the log directory if needed
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create main file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_file_size_mb * 1024 * 1024,
        backupCount=backup_count
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Create error file handler if specified
    if error_log_file:
        # Create error log directory if needed
        error_log_dir = os.path.dirname(error_log_file)
        if error_log_dir and not os.path.exists(error_log_dir):
            os.makedirs(error_log_dir)
            
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)  # Only ERROR and CRITICAL
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)
    
    return logger