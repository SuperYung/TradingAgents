# Fundamental Data Tools Migration - Fix Documentation

## Problem

The fundamental analyst was failing with:
```
RuntimeError: All vendor implementations failed for method 'get_fundamentals'
```

This error occurred because the old `route_to_vendor` system in `interface.py` was trying to use alpha_vantage and openai vendors that were not properly configured or available.

## Solution

Migrated the fundamental data tools to use the new **DataSourceManager** system with multi-provider support and automatic fallback.

### Changes Made

#### 1. Updated `tradingagents/agents/utils/fundamental_data_tools.py`

**Before:**
```python
from tradingagents.dataflows.interface import route_to_vendor

@tool
def get_fundamentals(ticker, curr_date):
    return route_to_vendor("get_fundamentals", ticker, curr_date)
```

**After:**
```python
from tradingagents.dataflows.data_source_manager import DataSourceManager
import asyncio

_data_manager = None

def get_data_manager() -> DataSourceManager:
    global _data_manager
    if _data_manager is None:
        _data_manager = DataSourceManager()
    return _data_manager

@tool
def get_fundamentals(ticker, curr_date):
    manager = get_data_manager()
    data = asyncio.run(manager.get_fundamentals(ticker))
    if not data:
        return f"Unable to retrieve fundamental data for {ticker}..."
    return format_fundamentals_report(data, ticker)
```

**Key Improvements:**
- ✅ Uses new multi-provider DataSourceManager
- ✅ Automatic fallback between providers (YahooFinance → Google → AlphaVantage)
- ✅ Better error handling (returns informative message instead of RuntimeError)
- ✅ Formatted output with readable report structure

#### 2. Updated Other Functions

Also migrated:
- `get_balance_sheet()` - now uses yfinance directly
- `get_cashflow()` - now uses yfinance directly  
- `get_income_statement()` - now uses yfinance directly

These functions bypass the old routing system and call yfinance implementations directly from `tradingagents/dataflows/y_finance.py`.

## Setup Requirements

### Install Required Dependencies

The fundamental data tools now require `yfinance` to be installed:

```bash
# Install dependencies
pip install -r requirements.txt

# Or install yfinance specifically
pip install yfinance
```

### Provider Configuration

Configure providers in `config/data_sources.toml`:

```toml
[providers.yfinance]
enabled = true
priority = 2  # Lower number = higher priority
cache_ttl = 3600

[providers.alphavantage]
enabled = true
priority = 1
cache_ttl = 3600

[providers.google]
enabled = false  # Google doesn't support fundamentals yet
priority = 3
cache_ttl = 3600
```

### Optional: API Keys

For enhanced data access, set these environment variables:

```bash
# Alpha Vantage (recommended for fundamentals)
export ALPHA_VANTAGE_API_KEY="your_key_here"

# Google Finance (for news and quotes)
export GOOGLE_API_KEY="your_key_here"
```

## Testing

Run the test script to verify the fix:

```bash
python3 test_fundamental_fix.py
```

Expected output:
```
✅ Created DataSourceManager with N providers
✅ Successfully retrieved fundamental data!
   Data source: yfinance
   Symbol: NFLX
   P/E Ratio: 45.23
```

## How It Works

1. **DataSourceManager** initializes all available providers
2. Providers are sorted by priority (lower number = higher priority)
3. When `get_fundamentals()` is called:
   - Manager tries each provider in priority order
   - If a provider fails, automatically falls back to next
   - Returns first successful result
   - If all fail, returns None (gracefully handled)

4. The tool function formats the data into a readable report

## Benefits

✅ **No More RuntimeError** - Graceful degradation instead of crashes  
✅ **Multi-Source** - Automatic fallback between providers  
✅ **Better Logging** - Clear visibility into which provider succeeded  
✅ **Configurable** - Easy to enable/disable providers via config  
✅ **Cacheable** - Built-in TTL caching for performance  
✅ **Testable** - Clean separation of concerns  

## Migration Notes

- The old `route_to_vendor` system in `interface.py` is still used by other tools (news, technical indicators) and should be migrated separately
- This fix specifically addresses fundamental data tools used by the **Fundamentals Analyst** agent
- The new system is backward compatible - if yfinance is not installed, it gracefully falls back to other providers or returns informative error messages

## Related Files

- `tradingagents/agents/utils/fundamental_data_tools.py` - Updated tool implementations
- `tradingagents/dataflows/data_source_manager.py` - Multi-provider orchestration
- `tradingagents/dataflows/providers/us/yfinance_provider.py` - YahooFinance implementation
- `config/data_sources.toml` - Provider configuration
- `docs/DATA_SOURCES_GUIDE.md` - Complete data sources documentation

