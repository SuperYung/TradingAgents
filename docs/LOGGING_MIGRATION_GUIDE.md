# TradingAgents Logging System Migration Guide

## Overview

TradingAgents has been upgraded with an enterprise-grade logging system that provides:
- Multiple log handlers (console, file, error, structured)
- Colored console output using ANSI codes
- Rotating file handlers (10MB max, 5 backups)
- Separate error.log for WARNING+ level messages
- TOML/JSON configuration file support
- Environment variable configuration
- Session tracking (session_id, stock_symbol, analysis_type)
- Cost/token tracking for LLM calls

## Architecture

### Core Components

1. **`tradingagents/utils/logging_manager.py`** - Main logging manager
   - `TradingAgentsLogger` - Core logging manager class
   - `ColoredFormatter` - Colored console output formatter
   - `StructuredFormatter` - JSON structured logging formatter
   - Convenience functions: `get_logger()`, `setup_logging()`

2. **`config/logging.toml`** - Configuration file
   - Logging levels
   - Handler configuration
   - Logger-specific settings
   - Performance and security settings

3. **Log Files** (in `./logs/` by default)
   - `tradingagents.log` - All logs (DEBUG+)
   - `error.log` - Errors only (WARNING+)
   - `tradingagents_structured.log` - JSON format (optional)

## Quick Start

### Basic Usage

```python
from tradingagents.utils.logging_manager import get_logger

# Get a logger
logger = get_logger("tradingagents.mymodule")

# Use it
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### With Session Tracking

```python
from tradingagents.utils.logging_manager import get_logger
import uuid

logger = get_logger("tradingagents.graph")
session_id = str(uuid.uuid4())

logger.info(
    "Starting analysis",
    extra={
        'session_id': session_id,
        'stock_symbol': 'AAPL',
        'analysis_type': 'technical'
    }
)
```

### Advanced Helper Methods

The logging manager provides specialized helper methods:

```python
from tradingagents.utils.logging_manager import get_logger_manager

logger_manager = get_logger_manager()
logger = logger_manager.get_logger("tradingagents.agents")

# Log analysis start
logger_manager.log_analysis_start(
    logger=logger,
    stock_symbol="AAPL",
    analysis_type="technical",
    session_id=session_id
)

# Log analysis complete
logger_manager.log_analysis_complete(
    logger=logger,
    stock_symbol="AAPL",
    analysis_type="technical",
    session_id=session_id,
    duration=12.5,
    cost=0.0023
)

# Log agent execution
logger_manager.log_agent_start(
    logger=logger,
    agent_name="market_analyst",
    stock_symbol="AAPL",
    session_id=session_id
)

logger_manager.log_agent_complete(
    logger=logger,
    agent_name="market_analyst",
    stock_symbol="AAPL",
    session_id=session_id,
    duration=3.2,
    success=True,
    result_length=1500
)

# Log token usage
logger_manager.log_token_usage(
    logger=logger,
    provider="openai",
    model="gpt-4",
    input_tokens=1000,
    output_tokens=500,
    cost=0.0023,
    session_id=session_id
)
```

## Migration Steps

### Step 1: Replace print() Statements

**Before:**
```python
print(f"Starting analysis for {stock}")
print(f"Error: {error}")
```

**After:**
```python
from tradingagents.utils.logging_manager import get_logger

logger = get_logger(__name__)

logger.info(f"Starting analysis for {stock}")
logger.error(f"Error: {error}")
```

### Step 2: Add Session Tracking to Graph

**In `trading_graph.py`:**
```python
import uuid
from tradingagents.utils.logging_manager import get_logger

class TradingAgentsGraph:
    def __init__(self, ...):
        self.logger = get_logger("tradingagents.graph")
        self.session_id = str(uuid.uuid4())
        
    def propagate(self, company_name, trade_date):
        self.logger.info(
            f"Starting analysis - Stock: {company_name}",
            extra={
                'stock_symbol': company_name,
                'session_id': self.session_id,
                'trade_date': str(trade_date)
            }
        )
```

### Step 3: Add Cost Tracking to LLM Calls

When making LLM calls, track token usage:

```python
# After LLM call
if hasattr(response, 'usage'):
    logger_manager.log_token_usage(
        logger=logger,
        provider="openai",
        model="gpt-4",
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
        cost=calculate_cost(response.usage),
        session_id=session_id
    )
```

## Configuration

### Using TOML Configuration

Edit `config/logging.toml`:

```toml
[logging]
level = "INFO"

[logging.handlers.console]
enabled = true
colored = true
level = "INFO"

[logging.handlers.file]
enabled = true
level = "DEBUG"
max_size = "10MB"
backup_count = 5
directory = "./logs"
```

### Using Environment Variables

```bash
export TRADINGAGENTS_LOG_LEVEL=DEBUG
export TRADINGAGENTS_LOG_DIR=/var/log/tradingagents
```

### Programmatic Configuration

```python
from tradingagents.utils.logging_manager import setup_logging

config = {
    'level': 'DEBUG',
    'handlers': {
        'console': {'enabled': True, 'colored': True, 'level': 'INFO'},
        'file': {'enabled': True, 'level': 'DEBUG', 'max_size': '10MB', 'backup_count': 5, 'directory': './logs'}
    }
}

setup_logging(config)
```

## Log Levels

Use appropriate log levels:

- **DEBUG** - Detailed diagnostic information (verbose)
- **INFO** - General informational messages (default)
- **WARNING** - Warning messages (potential issues)
- **ERROR** - Error messages (failures)
- **CRITICAL** - Critical errors (system failures)

### Guidelines

```python
logger.debug("Detailed debugging information")
logger.info("Normal operation, important events")
logger.warning("Something unexpected but recoverable")
logger.error("Error occurred, operation failed")
logger.critical("System failure, immediate attention required")
```

## Features

### 1. Colored Console Output

Console output uses ANSI color codes:
- DEBUG: Cyan
- INFO: Green
- WARNING: Yellow
- ERROR: Red
- CRITICAL: Magenta

Automatically disabled when output is redirected to a file.

### 2. Log Rotation

Logs automatically rotate when they exceed 10MB (configurable):
- `tradingagents.log` → `tradingagents.log.1` → `tradingagents.log.2` ...
- Keeps 5 backup files by default

### 3. Error Log Separation

WARNING and above messages are automatically written to `error.log` for easy error monitoring.

### 4. Structured Logging (Optional)

Enable JSON structured logging for machine-readable logs:

```toml
[logging.handlers.structured]
enabled = true
level = "INFO"
directory = "./logs"
```

Output format:
```json
{
  "timestamp": "2026-01-03T10:30:45.123456",
  "level": "INFO",
  "logger": "tradingagents.graph",
  "message": "Starting analysis",
  "module": "trading_graph",
  "function": "propagate",
  "line": 165,
  "session_id": "abc-123",
  "stock_symbol": "AAPL"
}
```

### 5. Session Tracking

Use session IDs to track related log messages:

```python
import uuid
session_id = str(uuid.uuid4())

logger.info("Message", extra={'session_id': session_id})
```

### 6. Performance Monitoring

Track slow operations automatically:

```toml
[logging.performance]
enabled = true
log_slow_operations = true
slow_threshold_seconds = 5.0
```

## Best Practices

### 1. Logger Naming

Use module-based naming:
```python
logger = get_logger(__name__)  # Best practice
logger = get_logger("tradingagents.agents.analysts")  # Explicit
```

### 2. Contextual Information

Always include relevant context:
```python
logger.info(
    "Analysis complete",
    extra={
        'stock_symbol': symbol,
        'duration': duration,
        'cost': cost
    }
)
```

### 3. Exception Logging

Always log exceptions with traceback:
```python
try:
    # ... code ...
except Exception as e:
    logger.error(f"Failed to process: {e}", exc_info=True)
    raise
```

### 4. Sensitive Data

Never log sensitive information:
- API keys
- Passwords
- Personal identification information

### 5. Performance

- Use appropriate log levels (avoid excessive DEBUG logs in production)
- Use lazy formatting: `logger.debug("Value: %s", expensive_call())` instead of f-strings for DEBUG

## Troubleshooting

### Logs Not Appearing

1. Check log level configuration
2. Verify handlers are enabled
3. Check file permissions for log directory
4. Ensure TOML library is installed: `pip install toml`

### Missing Colors

Colors only work in TTY terminals. When output is redirected, colors are automatically disabled.

### Log Files Growing Too Large

Adjust rotation settings in `config/logging.toml`:

```toml
[logging.handlers.file]
max_size = "5MB"  # Smaller files
backup_count = 10  # More backups
```

## Backwards Compatibility

The logging system is designed to be backwards compatible:

1. **JSON State Logs**: The existing JSON state logging in `_log_state()` continues to work alongside the new logging system
2. **Print Statements**: Existing print statements have been replaced with appropriate logger calls
3. **Configuration**: If no configuration file is found, sensible defaults are used

## Testing

Run the test suite to verify logging functionality:

```bash
python -m pytest tests/test_logging.py
```

Manual testing:

```python
from tradingagents.utils.logging_manager import get_logger

logger = get_logger("test")
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")

# Check ./logs/tradingagents.log and ./logs/error.log
```

## Additional Resources

- **Source Code**: `tradingagents/utils/logging_manager.py`
- **Configuration**: `config/logging.toml`
- **Python Logging Docs**: https://docs.python.org/3/library/logging.html

## Support

For issues or questions:
1. Check this guide
2. Review the configuration file
3. Check log files for error messages
4. Open an issue on GitHub

---

**Version**: 1.0.0  
**Last Updated**: January 3, 2026

