# Debugging Cache Key Mismatch

## Issue
Redis keys are increasing but hits remain at 0 = cache key mismatch between SET and GET operations.

## Step 1: Enable Debug Logging

Edit your `.env` file:
```bash
LOG_LEVEL=DEBUG
```

## Step 2: Run Diagnostic Tool

```bash
# Make sure you're in the project root directory
cd /path/to/TradingAgents

# Check current cache state
python -m tradingagents.utils.cache_debug --compare
```

**What to look for**:
- If "Keys exist but no hits!" appears, you have a key mismatch

## Step 3: Inspect Redis Keys

```bash
# See all cached keys and their details
python -m tradingagents.utils.cache_debug --inspect
```

This shows:
- All Redis keys
- Their TTL
- Their content type and size

## Step 4: Run Analysis with Debug Logging

```bash
python cli/main.py
```

**Look for these lines** in the output:

### When READING from cache (GET):
```
DEBUG: 🔎 Alpha Vantage GET - Function: OVERVIEW, Params: {'function': 'OVERVIEW', 'vendor': 'alpha_vantage', 'symbol': 'AAPL'}
DEBUG: 🔑 Generated cache key: fundamentals:function=OVERVIEW:symbol=AAPL:vendor=alpha_vantage
DEBUG: 🔍 Looking up Redis key: ta:a1b2c3d4e5f6g7h8
DEBUG: ❌ Redis MISS: ta:a1b2c3d4e5f6g7h8 not found
```

### When WRITING to cache (SET):
```
DEBUG: 🌐 API Request: OVERVIEW AAPL
DEBUG: 💾 Alpha Vantage SET - Function: OVERVIEW, Params: {'function': 'OVERVIEW', 'vendor': 'alpha_vantage', 'symbol': 'AAPL', 'outputsize': 'compact'}
DEBUG: 🔑 Generated cache key: fundamentals:function=OVERVIEW:outputsize=compact:symbol=AAPL:vendor=alpha_vantage
DEBUG: 💾 Storing in Redis key: ta:x9y8z7w6v5u4t3s2
INFO: ✅ Redis SET successful: fundamentals
```

## Step 5: Compare the Params

**Problem Example**:
- GET params: `{'function': 'OVERVIEW', 'vendor': 'alpha_vantage', 'symbol': 'AAPL'}`
- SET params: `{'function': 'OVERVIEW', 'vendor': 'alpha_vantage', 'symbol': 'AAPL', 'outputsize': 'compact'}`

**Notice**: SET has extra param `outputsize` that GET doesn't have!

This causes different cache keys:
- GET key: `fundamentals:function=OVERVIEW:symbol=AAPL:vendor=alpha_vantage`
- SET key: `fundamentals:function=OVERVIEW:outputsize=compact:symbol=AAPL:vendor=alpha_vantage`

Different keys = no cache hits!

## Step 6: Clear Cache and Test Fix

After identifying the issue:

```bash
# Clear Redis to start fresh
python -m tradingagents.utils.cache_debug --clear

# Run analysis again
python cli/main.py

# Check if hits are now working
python -m tradingagents.utils.cache_monitor --stats
```

## Common Causes

1. **Extra params during API call**: `outputsize`, `datatype`, `source`, etc.
2. **Case sensitivity**: `AAPL` vs `aapl`
3. **Date format differences**: `2024-01-01` vs `2024/01/01`
4. **Order of params** (should be handled by sorting, but check)
5. **Type differences**: `symbol='AAPL'` vs `symbol=['AAPL']`

## Expected Output After Fix

```
DEBUG: 🔎 Alpha Vantage GET - Params: {'function': 'OVERVIEW', 'symbol': 'AAPL', 'vendor': 'alpha_vantage'}
DEBUG: 🔑 Generated cache key: fundamentals:function=OVERVIEW:symbol=AAPL:vendor=alpha_vantage
DEBUG: 🔍 Looking up Redis key: ta:a1b2c3d4e5f6g7h8
INFO: ✅ Redis HIT: fundamentals {'symbol': 'AAPL'}
```

Then check stats:
```
🔴 Redis:
  Hits: 5          ← Should increase!
  Keys: 5
  Memory: 2.5MB
```

## Quick Commands

```bash
# 1. Enable debug
# Edit .env: LOG_LEVEL=DEBUG

# 2. Check current state
python -m tradingagents.utils.cache_debug --compare

# 3. Inspect keys
python -m tradingagents.utils.cache_debug --inspect

# 4. Run analysis (watch for key mismatches in logs)
python cli/main.py

# 5. Clear cache if needed
python -m tradingagents.utils.cache_debug --clear

# 6. Check stats
python -m tradingagents.utils.cache_monitor --stats
```

## Next Steps

Once you've identified the mismatch from the debug logs, let me know:
1. What params appear in GET
2. What params appear in SET
3. Which params are different

I'll fix the code to ensure consistent params!

