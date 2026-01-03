#!/usr/bin/env python3
"""
Unified Logging Manager for TradingAgents
Provides enterprise-grade logging capabilities with multiple handlers,
colored output, rotation, and structured logging support.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import json

try:
    import toml
except ImportError:
    toml = None


# Bootstrap logger for initialization logging
_bootstrap_logger = logging.getLogger("tradingagents.logging_manager")


class ColoredFormatter(logging.Formatter):
    """Colored log formatter using ANSI color codes."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to level name
        if hasattr(record, 'levelname') and record.levelname in self.COLORS:
            levelname = record.levelname
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        return super().format(record)


class StructuredFormatter(logging.Formatter):
    """Structured log formatter (JSON format)."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        if hasattr(record, 'analysis_type'):
            log_entry['analysis_type'] = record.analysis_type
        if hasattr(record, 'stock_symbol'):
            log_entry['stock_symbol'] = record.stock_symbol
        if hasattr(record, 'cost'):
            log_entry['cost'] = record.cost
        if hasattr(record, 'tokens'):
            log_entry['tokens'] = record.tokens
        if hasattr(record, 'duration'):
            log_entry['duration'] = record.duration
            
        return json.dumps(log_entry, ensure_ascii=False)


class TradingAgentsLogger:
    """TradingAgents unified logging manager."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the logging manager.
        
        Args:
            config: Optional configuration dictionary. If None, loads from file or uses defaults.
        """
        self.config = config or self._load_default_config()
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_logging()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default logging configuration."""
        # Try to load from config file
        config = self._load_config_file()
        if config:
            return config

        # Get configuration from environment variables
        log_level = os.getenv('TRADINGAGENTS_LOG_LEVEL', 'INFO').upper()
        log_dir = os.getenv('TRADINGAGENTS_LOG_DIR', './logs')

        return {
            'level': log_level,
            'format': {
                'console': '%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
                'file': '%(asctime)s | %(name)-20s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d | %(message)s',
                'structured': 'json'
            },
            'handlers': {
                'console': {
                    'enabled': True,
                    'colored': True,
                    'level': log_level
                },
                'file': {
                    'enabled': True,
                    'level': 'DEBUG',
                    'max_size': '10MB',
                    'backup_count': 5,
                    'directory': log_dir
                },
                'error': {
                    'enabled': True,
                    'level': 'WARNING',  # Only WARNING and above
                    'max_size': '10MB',
                    'backup_count': 5,
                    'directory': log_dir,
                    'filename': 'error.log'
                },
                'structured': {
                    'enabled': False,  # Disabled by default
                    'level': 'INFO',
                    'directory': log_dir
                }
            },
            'loggers': {
                'tradingagents': {'level': log_level},
                'urllib3': {'level': 'WARNING'},
                'requests': {'level': 'WARNING'},
                'matplotlib': {'level': 'WARNING'}
            }
        }

    def _load_config_file(self) -> Optional[Dict[str, Any]]:
        """Load logging configuration from file."""
        if toml is None:
            _bootstrap_logger.info("TOML library not available, using default configuration")
            return None
            
        # Check for config files
        config_paths = [
            'config/logging.toml',
            './logging.toml'
        ]

        for config_path in config_paths:
            if Path(config_path).exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = toml.load(f)

                    # Convert config format
                    return self._convert_toml_config(config_data)
                except Exception as e:
                    _bootstrap_logger.warning(f"Warning: Unable to load config file {config_path}: {e}")
                    continue

        return None

    def _convert_toml_config(self, toml_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert TOML configuration to internal format."""
        logging_config = toml_config.get('logging', {})

        return {
            'level': logging_config.get('level', 'INFO'),
            'format': logging_config.get('format', {}),
            'handlers': logging_config.get('handlers', {}),
            'loggers': logging_config.get('loggers', {}),
            'performance': logging_config.get('performance', {}),
            'security': logging_config.get('security', {})
        }
    
    def _setup_logging(self):
        """Setup the logging system."""
        # Create log directory if file handler is enabled
        if self.config['handlers']['file']['enabled']:
            log_dir = Path(self.config['handlers']['file']['directory'])
            log_dir.mkdir(parents=True, exist_ok=True)
        
        # Set root logger level
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config['level']))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Add handlers
        self._add_console_handler(root_logger)
        self._add_file_handler(root_logger)
        self._add_error_handler(root_logger)
        
        if self.config['handlers']['structured']['enabled']:
            self._add_structured_handler(root_logger)
        
        # Configure specific loggers
        self._configure_specific_loggers()
    
    def _add_console_handler(self, logger: logging.Logger):
        """Add console handler."""
        if not self.config['handlers']['console']['enabled']:
            return
            
        console_handler = logging.StreamHandler(sys.stdout)
        console_level = getattr(logging, self.config['handlers']['console']['level'])
        console_handler.setLevel(console_level)
        
        # Choose formatter
        console_format = self.config['format'].get('console', 
            '%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s')
        
        if self.config['handlers']['console']['colored'] and sys.stdout.isatty():
            formatter = ColoredFormatter(console_format)
        else:
            formatter = logging.Formatter(console_format)
        
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    def _add_file_handler(self, logger: logging.Logger):
        """Add rotating file handler."""
        if not self.config['handlers']['file']['enabled']:
            return

        log_dir = Path(self.config['handlers']['file']['directory'])
        log_file = log_dir / 'tradingagents.log'

        # Use RotatingFileHandler for log rotation
        max_size = self._parse_size(self.config['handlers']['file']['max_size'])
        backup_count = self.config['handlers']['file']['backup_count']

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )

        file_level = getattr(logging, self.config['handlers']['file']['level'])
        file_handler.setLevel(file_level)

        file_format = self.config['format'].get('file',
            '%(asctime)s | %(name)-20s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d | %(message)s')
        formatter = logging.Formatter(file_format)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    def _add_error_handler(self, logger: logging.Logger):
        """Add error log handler (WARNING and above only)."""
        error_config = self.config['handlers'].get('error', {})
        if not error_config.get('enabled', True):
            return

        log_dir = Path(error_config.get('directory', self.config['handlers']['file']['directory']))
        error_log_file = log_dir / error_config.get('filename', 'error.log')

        # Use RotatingFileHandler for log rotation
        max_size = self._parse_size(error_config.get('max_size', '10MB'))
        backup_count = error_config.get('backup_count', 5)

        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )

        # Only log WARNING and above (WARNING, ERROR, CRITICAL)
        error_level = getattr(logging, error_config.get('level', 'WARNING'))
        error_handler.setLevel(error_level)

        file_format = self.config['format'].get('file',
            '%(asctime)s | %(name)-20s | %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d | %(message)s')
        formatter = logging.Formatter(file_format)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
    
    def _add_structured_handler(self, logger: logging.Logger):
        """Add structured log handler (JSON format)."""
        log_dir = Path(self.config['handlers']['structured']['directory'])
        log_file = log_dir / 'tradingagents_structured.log'
        
        structured_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self._parse_size('10MB'),
            backupCount=3,
            encoding='utf-8'
        )
        
        structured_level = getattr(logging, self.config['handlers']['structured']['level'])
        structured_handler.setLevel(structured_level)
        
        formatter = StructuredFormatter()
        structured_handler.setFormatter(formatter)
        logger.addHandler(structured_handler)
    
    def _configure_specific_loggers(self):
        """Configure specific loggers."""
        for logger_name, logger_config in self.config['loggers'].items():
            logger = logging.getLogger(logger_name)
            level = getattr(logging, logger_config['level'])
            logger.setLevel(level)
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string (e.g., '10MB') to bytes."""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger by name.
        
        Args:
            name: Logger name
            
        Returns:
            Logger instance
        """
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)
        return self.loggers[name]
    
    def log_analysis_start(self, logger: logging.Logger, stock_symbol: str, 
                          analysis_type: str, session_id: str):
        """Log analysis start event.
        
        Args:
            logger: Logger instance
            stock_symbol: Stock ticker symbol
            analysis_type: Type of analysis
            session_id: Unique session identifier
        """
        logger.info(
            f"🚀 Starting analysis - Stock: {stock_symbol}, Type: {analysis_type}",
            extra={
                'stock_symbol': stock_symbol,
                'analysis_type': analysis_type,
                'session_id': session_id,
                'event_type': 'analysis_start',
                'timestamp': datetime.now().isoformat()
            }
        )

    def log_analysis_complete(self, logger: logging.Logger, stock_symbol: str, 
                            analysis_type: str, session_id: str, duration: float, 
                            cost: float = 0):
        """Log analysis completion event.
        
        Args:
            logger: Logger instance
            stock_symbol: Stock ticker symbol
            analysis_type: Type of analysis
            session_id: Unique session identifier
            duration: Analysis duration in seconds
            cost: Analysis cost in dollars
        """
        logger.info(
            f"✅ Analysis complete - Stock: {stock_symbol}, Duration: {duration:.2f}s, Cost: ${cost:.4f}",
            extra={
                'stock_symbol': stock_symbol,
                'analysis_type': analysis_type,
                'session_id': session_id,
                'duration': duration,
                'cost': cost,
                'event_type': 'analysis_complete',
                'timestamp': datetime.now().isoformat()
            }
        )

    def log_agent_start(self, logger: logging.Logger, agent_name: str, 
                       stock_symbol: str, session_id: str, **extra_data):
        """Log agent start event.
        
        Args:
            logger: Logger instance
            agent_name: Name of the agent
            stock_symbol: Stock ticker symbol
            session_id: Unique session identifier
            **extra_data: Additional data to log
        """
        logger.info(
            f"📊 [Agent Start] {agent_name} - Stock: {stock_symbol}",
            extra={
                'agent_name': agent_name,
                'stock_symbol': stock_symbol,
                'session_id': session_id,
                'event_type': 'agent_start',
                'timestamp': datetime.now().isoformat(),
                **extra_data
            }
        )

    def log_agent_complete(self, logger: logging.Logger, agent_name: str, 
                          stock_symbol: str, session_id: str, duration: float, 
                          success: bool = True, result_length: int = 0, **extra_data):
        """Log agent completion event.
        
        Args:
            logger: Logger instance
            agent_name: Name of the agent
            stock_symbol: Stock ticker symbol
            session_id: Unique session identifier
            duration: Agent execution duration in seconds
            success: Whether the agent succeeded
            result_length: Length of the result
            **extra_data: Additional data to log
        """
        status = "✅ Success" if success else "❌ Failed"
        logger.info(
            f"📊 [Agent Complete] {agent_name} - {status} - Stock: {stock_symbol}, Duration: {duration:.2f}s",
            extra={
                'agent_name': agent_name,
                'stock_symbol': stock_symbol,
                'session_id': session_id,
                'duration': duration,
                'success': success,
                'result_length': result_length,
                'event_type': 'agent_complete',
                'timestamp': datetime.now().isoformat(),
                **extra_data
            }
        )

    def log_agent_error(self, logger: logging.Logger, agent_name: str, 
                       stock_symbol: str, session_id: str, duration: float, 
                       error: str, **extra_data):
        """Log agent error event.
        
        Args:
            logger: Logger instance
            agent_name: Name of the agent
            stock_symbol: Stock ticker symbol
            session_id: Unique session identifier
            duration: Agent execution duration in seconds
            error: Error message
            **extra_data: Additional data to log
        """
        logger.error(
            f"❌ [Agent Error] {agent_name} - Stock: {stock_symbol}, Duration: {duration:.2f}s, Error: {error}",
            extra={
                'agent_name': agent_name,
                'stock_symbol': stock_symbol,
                'session_id': session_id,
                'duration': duration,
                'error': error,
                'event_type': 'agent_error',
                'timestamp': datetime.now().isoformat(),
                **extra_data
            },
            exc_info=True
        )
    
    def log_token_usage(self, logger: logging.Logger, provider: str, model: str, 
                       input_tokens: int, output_tokens: int, cost: float, 
                       session_id: str):
        """Log token usage event.
        
        Args:
            logger: Logger instance
            provider: LLM provider name
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost: Cost in dollars
            session_id: Unique session identifier
        """
        logger.info(
            f"📊 Token usage - {provider}/{model}: Input={input_tokens}, Output={output_tokens}, Cost=${cost:.6f}",
            extra={
                'provider': provider,
                'model': model,
                'tokens': {'input': input_tokens, 'output': output_tokens},
                'cost': cost,
                'session_id': session_id,
                'event_type': 'token_usage'
            }
        )


# Global logger manager instance
_logger_manager: Optional[TradingAgentsLogger] = None


def get_logger_manager() -> TradingAgentsLogger:
    """Get the global logger manager instance.
    
    Returns:
        TradingAgentsLogger instance
    """
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = TradingAgentsLogger()
    return _logger_manager


def get_logger(name: str) -> logging.Logger:
    """Get a logger by name (convenience function).
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return get_logger_manager().get_logger(name)


def setup_logging(config: Optional[Dict[str, Any]] = None):
    """Setup the project logging system (convenience function).
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        TradingAgentsLogger instance
    """
    global _logger_manager
    _logger_manager = TradingAgentsLogger(config)
    return _logger_manager

