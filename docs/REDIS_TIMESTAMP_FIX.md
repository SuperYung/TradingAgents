# Redis Timestamp Serialization Fix

## Issue Discovered
```
Redis set error: keys must be str, int, float, bool or None, not Timestamp
```

Found in logs when trying to cache news data.

## Root Cause

### Problem
Redis's `json.dumps()` couldn't serialize pandas `Timestamp` objects in dictionary keys or values.

When Alpha Vantage returns news with datetime fields, they may get converted to pandas `Timestamp` objects during processing. Redis cache fails silently.

### Impact
- ❌ News data not cached in Redis (L2)
- ⚠️ News still reaches MongoDB save code (separate from caching)
- ⚠️ But if there are other serialization issues, could affect news save

## The Fix

### Before (integrated_cache.py line ~277)
```python
self.redis.setex(
    redis_key,
    ttl,
    json.dumps(data, default=str)  # ❌ Only converts values, not keys
)
```

### After
```python
import pandas as pd

def convert_to_serializable(obj):
    """Convert non-serializable types to strings"""
    if isinstance(obj, (pd.Timestamp, pd.Timedelta)):
        return str(obj)
    elif isinstance(obj, dict):
        # Convert BOTH keys and values
        return {str(k): convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    else:
        return obj

serializable_data = convert_to_serializable(data)

self.redis.setex(
    redis_key,
    ttl,
    json.dumps(serializable_data, default=str)  # ✅ Now handles Timestamps
)
```

## What This Fixes

### 1. Pandas Timestamp Objects
```python
# Before: TypeError
{pd.Timestamp('2024-01-01'): 'value'}

# After: Works
{'2024-01-01 00:00:00': 'value'}
```

### 2. Nested Structures
```python
# Before: Fails on nested Timestamps
{'articles': [{'date': pd.Timestamp('2024-01-01')}]}

# After: Recursively converts all
{'articles': [{'date': '2024-01-01 00:00:00'}]}
```

### 3. Dictionary Keys
```python
# Before: "keys must be str"
{pd.Timestamp('2024-01-01'): {'data': 'value'}}

# After: Converts keys to strings
{'2024-01-01 00:00:00': {'data': 'value'}}
```

## Why News Should Still Save

The code flow in `alpha_vantage_common.py`:

```python
# Line 144: Cache (may fail with Timestamp error)
cache.set(data_type, response_json, **cache_params)

# Line 148: Save news (runs AFTER cache, independently)
if function_name == 'NEWS_SENTIMENT':
    news_saver.save_news_from_response(...)  # ← Still runs even if cache fails!
```

**Key point:** News MongoDB save is INDEPENDENT of Redis cache success.

So even with the Redis error, news should still save to MongoDB (unless there's a different issue).

## Testing

### 1. Check Redis Cache Now Works
```bash
# Run analysis
python -m cli.main

# Check logs - should NOT see Timestamp error
grep "Redis set error.*Timestamp" logs/tradingagents.log
```

Expected: No results (error gone)

### 2. Check News Saved
```bash
# Check MongoDB
python -m tradingagents.utils.mongo_monitor --stats
```

Expected:
```
📰 News Articles:
   Total Articles: 50+  ✅
```

### 3. Verify Redis Cache Works
```bash
# Check Redis has news keys
docker exec -it tradingagents-redis-1 redis-cli KEYS "ta:*" | grep -c "ta:"
```

Should see more keys than before.

## Additional Enhanced Logging

Added traceback logging to help diagnose future Redis issues:

```python
except Exception as e:
    logger.warning(f"Redis set error: {e}")
    import traceback
    logger.debug(f"Redis set traceback:\n{traceback.format_exc()}")
```

## Files Modified
- `tradingagents/dataflows/cache/integrated_cache.py`
  - Enhanced `_set_redis()` method
  - Recursive Timestamp conversion
  - Better error logging

## Common Timestamp Sources

These can all create pandas Timestamps:
- `pd.Timestamp('2024-01-01')`
- `pd.to_datetime('2024-01-01')`
- DataFrame index with dates
- Parsing datetime strings with pandas
- Alpha Vantage's `time_published` field

## Why `default=str` Wasn't Enough

```python
json.dumps(data, default=str)
```

This only handles:
- ✅ Values that can't be serialized
- ❌ Dictionary keys (must be strings BEFORE json.dumps)
- ❌ Objects that need pre-conversion

Our solution:
- ✅ Converts keys to strings
- ✅ Recursively processes nested structures
- ✅ Handles all pandas datetime types

## Date
2026-01-11

## Related Issues
- News not saving (separate issue being debugged)
- Cache serialization
- Pandas/Redis compatibility

