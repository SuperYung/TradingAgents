# MongoDB Data Type Mismatch Fix

## Issue
After fixing the CLI MongoDB save, only **analysis reports** were being saved (count: 1). Historical data, news, and token usage remained at 0.

## Root Cause: Data Type Mismatch

### The Problem
**integrated_cache.py** checked for specific data_type values:
```python
if data_type in ['historical', 'stock_data']:  # ❌ Too restrictive
```

But **y_finance.py** uses a different data_type:
```python
cache.get('historical_data', ...)  # ← 'historical_data' not in list!
cache.set('historical_data', ...)  # ← Never matches condition
```

Result: Historical data was **never saved to MongoDB** because the data_type didn't match!

## The Fix

Updated all three MongoDB checks in `integrated_cache.py`:

```python
# Before (line 138, 175, 223)
if data_type in ['historical', 'stock_data']:

# After
if data_type in ['historical', 'historical_data', 'stock_data']:
```

Now recognizes all three data type variations.

## Files Modified
- `tradingagents/dataflows/cache/integrated_cache.py` (3 locations)

## Testing
After this fix, run another analysis and check:
```bash
python -m tradingagents.utils.mongo_monitor --stats
```

Expected:
```
📊 Analysis Reports:
   Total Analyses: 2  ✅

📈 Historical Prices:
   Total Records: 500+  ✅ (now saving!)
   Unique Symbols: 2
```

## News & Token Usage Status

### News Articles (Still 0)
**Status:** Not implemented in TradingAgents  
**Reason:** TradingAgents-CN saves news through a dedicated `news_data_service`, not automatically during analysis.

**To implement (future):**
1. Create news aggregation during analysis
2. Call `NewsRepository.save_news()` with extracted articles
3. Add to analysis flow or as post-processing step

### Token Usage (Still 0)
**Status:** Not implemented  
**Reason:** LLM token tracking not hooked up to MongoDB yet.

**To implement (future):**
1. Track token usage during LLM calls
2. Call `UsageRepository.save_token_usage()` after each agent
3. Aggregate in analysis completion handler

## Priority

For US stock analysis (TradingAgents), the most important are:
1. ✅ **Analysis Reports** - WORKING
2. ✅ **Historical Prices** - FIXED (pending test)
3. ⏳ **News** - Optional (manual implementation needed)
4. ⏳ **Token Usage** - Nice-to-have (tracking not implemented)

## Date Fixed
2026-01-10

## Related
- CLI MongoDB Save Fix (analysis reports)
- Config Centralization
- PyMongo Boolean Fixes

