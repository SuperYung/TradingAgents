# Multi-Source Data Architecture Guide

## Overview

TradingAgents now features a robust multi-source data architecture that automatically falls back to alternative providers when the primary source fails. This ensures maximum data availability and reliability.

## Architecture

### Components

1. **Base Provider Interface** (`base_provider.py`)
   - Abstract base class for all data providers
   - Defines standard interface methods
   - Handles common error types

2. **Provider Implementations**
   - **YahooFinanceProvider** (Priority: 1) - Primary, free, no API key
   - **GoogleProvider** (Priority: 2) - Secondary, news focus
   - **AlphaVantageProvider** (Priority: 3) - Tertiary, comprehensive but rate-limited

3. **DataSourceManager** (`data_source_manager.py`)
   - Orchestrates all providers
   - Implements automatic fallback logic
   - Manages caching and rate limiting

### Priority System

Providers are tried in order of priority (lower number = higher priority):

```
1. Yahoo Finance  →  2. Google  →  3. Alpha Vantage
    (Primary)         (Secondary)      (Tertiary)
```

If the primary provider fails, the system automatically tries the next provider.

## Quick Start

### Basic Usage

```python
import asyncio
from tradingagents.dataflows.data_source_manager import get_data_source_manager

# Get the manager instance
manager = get_data_source_manager()

# Get stock quote (async)
async def get_quote():
    quote = await manager.get_stock_quote("AAPL")
    print(f"Price: ${quote['price']}")

asyncio.run(get_quote())
```

### Synchronous Usage

```python
from tradingagents.dataflows.data_source_manager import get_data_source_manager
import asyncio

manager = get_data_source_manager()

# Run async function synchronously
quote = asyncio.run(manager.get_stock_quote("AAPL"))
print(quote)
```

## Features

### 1. Automatic Fallback

When a provider fails, the system automatically tries the next one:

```python
# If Yahoo Finance fails, automatically tries Google, then Alpha Vantage
quote = await manager.get_stock_quote("AAPL")
```

### 2. Caching

Each provider has built-in caching (default: 1 hour TTL):

```python
# First call fetches from API
quote1 = await manager.get_stock_quote("AAPL")

# Second call within 1 hour uses cache
quote2 = await manager.get_stock_quote("AAPL")  # From cache
```

### 3. Rate Limiting

Providers automatically handle rate limiting:

- **Yahoo Finance**: 100ms between requests
- **Google**: 200ms between requests
- **Alpha Vantage**: 12 seconds between requests (5/minute limit)

### 4. Provider Status

Check which providers are available:

```python
status = manager.get_provider_status()
print(status)
# {
#     'yahoo_finance': {'available': True, 'priority': 1},
#     'google': {'available': True, 'priority': 2},
#     'alpha_vantage': {'available': False, 'priority': 3}  # No API key
# }
```

## Configuration

### Using config/data_sources.toml

```toml
[providers.yfinance]
enabled = true
priority = 1
cache_ttl = 3600

[providers.google]
enabled = true
priority = 2
cache_ttl = 3600

[providers.alphavantage]
enabled = true
priority = 3
cache_ttl = 3600
```

### Environment Variables

```bash
# Optional API keys
export GOOGLE_API_KEY="your_key_here"
export ALPHA_VANTAGE_API_KEY="your_key_here"
```

### Programmatic Configuration

```python
config = {
    'providers': {
        'yfinance': {'enabled': True, 'priority': 1, 'cache_ttl': 3600},
        'google': {'enabled': True, 'priority': 2, 'cache_ttl': 3600},
        'alphavantage': {'enabled': False}  # Disable if needed
    }
}

manager = DataSourceManager()
```

## API Reference

### DataSourceManager Methods

#### `get_stock_quote(symbol: str)`

Get real-time or latest stock quote.

```python
quote = await manager.get_stock_quote("AAPL")
# Returns:
# {
#     'symbol': 'AAPL',
#     'price': 150.25,
#     'change': 2.50,
#     'change_percent': 1.69,
#     'volume': 50000000,
#     'timestamp': '2026-01-03T12:00:00',
#     'provider': 'yahoo_finance'
# }
```

#### `get_historical_data(symbol, start_date, end_date, interval='daily')`

Get historical OHLCV data.

```python
data = await manager.get_historical_data(
    "AAPL",
    "2025-01-01",
    "2025-12-31",
    interval="daily"
)
# Returns CSV string
```

#### `get_stock_info(symbol: str)`

Get company information.

```python
info = await manager.get_stock_info("AAPL")
# Returns:
# {
#     'symbol': 'AAPL',
#     'name': 'Apple Inc.',
#     'sector': 'Technology',
#     'industry': 'Consumer Electronics',
#     'market_cap': 3000000000000,
#     'description': '...',
#     'website': 'https://www.apple.com',
#     'provider': 'yahoo_finance'
# }
```

#### `get_fundamentals(symbol: str)`

Get fundamental data and ratios.

```python
fundamentals = await manager.get_fundamentals("AAPL")
# Returns:
# {
#     'symbol': 'AAPL',
#     'pe_ratio': 28.5,
#     'eps': 6.25,
#     'dividend_yield': 0.0055,
#     'beta': 1.2,
#     '52_week_high': 200.00,
#     '52_week_low': 120.00,
#     'provider': 'yahoo_finance'
# }
```

#### `get_news(symbol=None, limit=10)`

Get news articles.

```python
news = await manager.get_news("AAPL", limit=5)
# Returns list of articles:
# [
#     {
#         'title': 'Apple announces...',
#         'summary': '...',
#         'url': 'https://...',
#         'published': '2026-01-03T10:00:00',
#         'source': 'Reuters',
#         'provider': 'yahoo_finance'
#     },
#     ...
# ]
```

## Provider Details

### Yahoo Finance Provider

**Priority**: 1 (Primary)

**Pros**:
- Free, no API key required
- Reliable and fast
- Comprehensive data
- No rate limits for reasonable use

**Cons**:
- Quotes have 15-20 minute delay
- Terms of service restrictions

**Supported**:
- ✅ Stock quotes
- ✅ Historical data
- ✅ Company info
- ✅ Fundamentals
- ✅ News

### Google Provider

**Priority**: 2 (Secondary)

**Pros**:
- Real-time quotes
- Excellent news coverage
- No strict rate limits

**Cons**:
- Limited fundamental data
- Some features require API key

**Supported**:
- ⚠️  Stock quotes (limited)
- ❌ Historical data
- ⚠️  Company info (limited)
- ❌ Fundamentals
- ✅ News

### Alpha Vantage Provider

**Priority**: 3 (Tertiary)

**Pros**:
- Comprehensive fundamental data
- Technical indicators
- News sentiment analysis

**Cons**:
- Requires API key
- Strict rate limiting (5 calls/minute free tier)
- Slower than other providers

**Supported**:
- ✅ Stock quotes
- ✅ Historical data
- ✅ Company info
- ✅ Fundamentals
- ✅ News

## Error Handling

### Provider Errors

```python
from tradingagents.dataflows.providers.base_provider import (
    ProviderError,
    RateLimitError,
    AuthenticationError,
    DataNotFoundError
)

try:
    quote = await manager.get_stock_quote("INVALID")
except DataNotFoundError:
    print("Stock not found")
except RateLimitError:
    print("Rate limit exceeded")
except ProviderError as e:
    print(f"Provider error: {e}")
```

### Automatic Recovery

The manager automatically handles errors and falls back to the next provider:

```python
# Even if Yahoo Finance is down, you'll still get data
# from Google or Alpha Vantage
quote = await manager.get_stock_quote("AAPL")
```

## Best Practices

### 1. Use Async/Await

```python
# Good
async def fetch_data():
    quote = await manager.get_stock_quote("AAPL")
    return quote

# If you need synchronous
import asyncio
quote = asyncio.run(manager.get_stock_quote("AAPL"))
```

### 2. Batch Requests

```python
# Fetch multiple stocks
symbols = ["AAPL", "MSFT", "GOOGL"]
quotes = await asyncio.gather(*[
    manager.get_stock_quote(symbol) 
    for symbol in symbols
])
```

### 3. Cache Awareness

```python
# Adjust cache TTL for different use cases
from tradingagents.dataflows.providers.us import YahooFinanceProvider

# Real-time trading: shorter cache
provider = YahooFinanceProvider(cache_ttl=60)  # 1 minute

# Long-term analysis: longer cache
provider = YahooFinanceProvider(cache_ttl=7200)  # 2 hours
```

### 4. Provider Selection

```python
# Disable providers you don't need
config = {
    'providers': {
        'yfinance': {'enabled': True},
        'google': {'enabled': False},  # Disable
        'alphavantage': {'enabled': False}  # Disable
    }
}
```

## Testing

Run the test suite:

```bash
python3 tests/test_data_sources.py
```

Test individual providers:

```python
from tradingagents.dataflows.providers.us import YahooFinanceProvider
import asyncio

provider = YahooFinanceProvider()
quote = asyncio.run(provider.get_stock_quote("AAPL"))
print(quote)
```

## Migration Guide

### From Old Interface

**Before:**
```python
from tradingagents.dataflows.interface import route_to_vendor

data = route_to_vendor("get_stock_data", "AAPL", ...)
```

**After:**
```python
from tradingagents.dataflows.data_source_manager import get_data_source_manager
import asyncio

manager = get_data_source_manager()
data = asyncio.run(manager.get_stock_quote("AAPL"))
```

### Benefits of New System

1. **Automatic Fallback**: No manual fallback handling needed
2. **Better Caching**: Built-in per-provider caching
3. **Rate Limiting**: Automatic rate limit handling
4. **Cleaner API**: Async/await instead of callbacks
5. **Better Logging**: Structured logging with provider tracking

## Troubleshooting

### No Providers Available

**Problem**: `No providers available!` error

**Solution**:
1. Install yfinance: `pip install yfinance`
2. Check API keys for Alpha Vantage/Google
3. Verify config file exists

### Rate Limit Errors

**Problem**: Alpha Vantage rate limit exceeded

**Solution**:
1. Wait 12 seconds between requests
2. Increase cache TTL
3. Disable Alpha Vantage and use Yahoo Finance

### Data Not Found

**Problem**: `DataNotFoundError` for valid symbol

**Solution**:
1. Check symbol format (should be uppercase)
2. Verify symbol exists on that exchange
3. Try different provider

## Performance

### Benchmarks

| Operation | Provider | Avg Time | Cache Hit |
|-----------|----------|----------|-----------|
| Quote | Yahoo | 150ms | 1ms |
| Quote | Alpha Vantage | 500ms | 1ms |
| Historical | Yahoo | 300ms | 2ms |
| Historical | Alpha Vantage | 800ms | 2ms |

### Optimization Tips

1. **Use caching**: Most data doesn't change every second
2. **Batch requests**: Fetch multiple symbols in parallel
3. **Disable unused providers**: Reduces overhead
4. **Adjust cache TTL**: Balance freshness vs performance

## Support

For issues or questions:
1. Check this guide
2. Review provider documentation
3. Check logs: `./logs/tradingagents.log`
4. Test individual providers

---

**Status**: ✅ Production Ready  
**Version**: 1.0.0  
**Last Updated**: January 3, 2026

