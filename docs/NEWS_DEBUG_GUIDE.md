# News Not Saving - Debug Guide

## Issue
Historical data saving works (758 records), but news articles remain at 0.

## Enhanced Logging Added

### What to Search For

#### 1. Check if news was fetched
```bash
grep -i "NEWS_SENTIMENT\|get_news" logs/tradingagents.log
```

#### 2. Check cache vs API
```bash
grep "📰 \[Cache HIT\]\|📰 \[API Response\]" logs/tradingagents.log
```

#### 3. Check NewsSaver activity
```bash
grep "📰 \[NewsSaver\]" logs/tradingagents.log
```

#### 4. Check what was extracted
```bash
grep "Extracted.*articles" logs/tradingagents.log
```

## Expected Log Flow (Working)

```
# When news is fetched
🌐 API Request: NEWS_SENTIMENT COST

# Cache check
📰 [Cache HIT] Attempting to save cached news to MongoDB...
   OR
📰 [API Response] Attempting to save news to MongoDB...

# NewsSaver processing
📰 [NewsSaver] save_news_from_response called
📰 [NewsSaver] enabled=True, repo=True, collection=<Collection>
📰 [NewsSaver] Processing news_data type=<class 'dict'>, symbol=COST
📰 [NewsSaver] News data keys: ['items', 'feed', ...]
📰 [NewsSaver] Extracted 50 articles

# Repository save
📰 Saving 50 news articles to MongoDB...
✅ Saved 50/50 news articles to MongoDB
```

## Possible Issues & Solutions

### Issue 1: News Never Fetched
**Symptom:** No "NEWS_SENTIMENT" in logs

**Cause:** Analysis didn't select News Analyst

**Solution:** Run analysis with News Analyst selected

### Issue 2: NewsSaver Disabled
**Symptom:** 
```
📰 [NewsSaver] Skipped - enabled=False
```

**Cause:** `MONGODB_SAVE_NEWS=false` or MongoDB disabled

**Solution:** Check `.env`:
```env
MONGODB_ENABLED=true
MONGODB_SAVE_NEWS=true
```

### Issue 3: Collection Not Available
**Symptom:**
```
📰 [NewsSaver] collection=None
```

**Cause:** NewsRepository didn't initialize properly

**Solution:** Check MongoDB connection, collection creation

### Issue 4: Wrong Data Format
**Symptom:**
```
📰 [NewsSaver] News data is <class 'str'>, not dict
```

**Cause:** Response is string, not parsed JSON

**Check:** Alpha Vantage might return error message as string

### Issue 5: No 'feed' Key
**Symptom:**
```
📰 [NewsSaver] News data keys: ['Information', ...]
📰 [NewsSaver] Extracted 0 articles
```

**Cause:** 
- API rate limit hit
- API returned error instead of news
- Different response format

**Solution:** Check response content in logs

### Issue 6: Cache Returns Data but Save Not Called
**Symptom:** 
- News data in cache
- No save attempt logs

**Cause:** We originally only saved on API response, not cache hits

**Solution:** ✅ Fixed! Now saves from both cache and API response

## Testing After Fix

### Run Analysis
```bash
python -m cli.main
# Select News Analyst
# Choose a stock symbol
```

### Check Logs
```bash
# See complete news flow
grep "📰" logs/tradingagents.log | tail -50

# Count save attempts
grep "save_news_from_response called" logs/tradingagents.log | wc -l

# Check extraction results
grep "Extracted.*articles" logs/tradingagents.log
```

### Verify MongoDB
```bash
python -m tradingagents.utils.mongo_monitor --stats
```

Should show:
```
📰 News Articles:
   Total Articles: 50+  ✅
```

## Manual Test (No Token Cost)

If you have cached news data:

```python
# test_news_save.py
from tradingagents.dataflows.news_saver import get_news_saver
from tradingagents.dataflows.cache import get_cache

cache = get_cache()

# Get cached news (if any)
cached_news = cache.get('news', tickers='COST', time_from='...', time_to='...', vendor='alpha_vantage')

if cached_news:
    print(f"Found cached news: {type(cached_news)}")
    
    # Try to save
    saver = get_news_saver()
    count = saver.save_news_from_response(cached_news, symbol='COST', source='alpha_vantage')
    print(f"Saved: {count} articles")
else:
    print("No cached news found")
```

## Files Modified
- `tradingagents/dataflows/alpha_vantage_common.py`
  - Added save on cache hit (line ~94)
  - Enhanced logging (lines ~137-149)

- `tradingagents/dataflows/news_saver.py`
  - Enhanced logging throughout
  - Better error messages

## Date
2026-01-11

