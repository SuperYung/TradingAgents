# Yahoo Finance News - Important Notes

## ⚠️ **Critical Limitation: Recent News Only**

**Yahoo Finance only provides recent news (approximately last 7 days).** It does NOT provide historical news.

### What This Means:

- ✅ **Analyzing today or recent dates**: Works great!
- ❌ **Analyzing historical dates (> 7 days ago)**: Returns empty or current news instead

### Example:

```python
# Today's date: 2025-12-30
ta.propagate("AAPL", "2025-12-30")  # ✅ Works - gets recent news
ta.propagate("AAPL", "2024-05-10")  # ❌ No news - date is 7+ months old
```

## Summary

Yahoo Finance news works great for **ticker-specific news** (e.g., AAPL, MSFT), but has limitations for **global market news** and **historical analysis**.

## What Works Well ✅

### Ticker-Specific News (`get_news`)
```python
# This works great - fast and reliable
ta = TradingAgentsGraph()
_, decision = ta.propagate("AAPL", "2024-05-10")
```

**Benefits:**
- ✅ Fast (1-2 seconds)
- ✅ Reliable
- ✅ No rate limits
- ✅ Good quality news

## What Has Limitations ⚠️

### Global Market News (`get_global_news`)

Yahoo Finance doesn't provide a direct "global news" feed. We've implemented a workaround that:
- Fetches news from major stocks (AAPL, MSFT, TSLA, JPM, XOM) as market proxies
- These companies are large enough that their news often reflects broader trends

**However, this may:**
- Return less comprehensive global coverage
- Occasionally fail if Yahoo Finance's API has issues
- Provide sector-biased news rather than truly global market news

## Recommended Solutions

### Option 1: Use Google for Global News (Recommended if you need comprehensive global coverage)

Edit your config or `default_config.py`:

```python
config = DEFAULT_CONFIG.copy()
config["tool_vendors"] = {
    "get_global_news": "google"  # Use Google scraping for global news
}

ta = TradingAgentsGraph(config=config)
```

**Trade-off:**
- ✅ Better global market coverage
- ❌ Slower (30-60 seconds due to web scraping)

### Option 2: Skip Global News Analysis

If global news isn't critical for your analysis:

```python
# Only analyze ticker-specific news
# The agents will work with company news only
ta = TradingAgentsGraph()
_, decision = ta.propagate("AAPL", "2024-05-10")
```

The news analyst will still get ticker-specific news, which is often sufficient.

### Option 3: Use Hybrid Approach (Best Balance)

Ticker news from Yahoo Finance (fast) + Global news from Google (comprehensive):

```python
config = DEFAULT_CONFIG.copy()
config["data_vendors"]["news_data"] = "yfinance"  # Default for ticker news
config["tool_vendors"] = {
    "get_global_news": "google"  # Override just for global news
}

ta = TradingAgentsGraph(config=config)
```

**Result:**
- Ticker-specific news: Fast (1-2 sec from Yahoo Finance)
- Global market news: Comprehensive (30-60 sec from Google)
- **Total time: ~30-60 seconds** (much better than all Google at 60-120 sec)

## Current Default Behavior

As of now:
- ✅ **Ticker news**: Yahoo Finance (fast, reliable)
- ⚠️ **Global news**: Yahoo Finance with proxy stocks (fast but limited coverage)

If global news fails, the system will:
1. Return a graceful error message
2. Continue with analysis using available data
3. Agents can still make decisions based on ticker-specific news

## Testing Global News

Test if Yahoo Finance global news works for you:

```python
from tradingagents.dataflows.y_finance import get_yfinance_global_news

# Try fetching global news
news = get_yfinance_global_news("2024-05-10", look_back_days=7, limit=5)
print(news)
```

If it returns an error or "Unable to fetch", switch to Google for global news.

## Recommendation for Production

For best results with free-tier APIs:

```python
from tradingagents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()

# Use Yahoo Finance for fast ticker-specific news
config["data_vendors"]["news_data"] = "yfinance"

# Override global news to use Google if comprehensive coverage is important
# Comment out the line below if you want to use Yahoo Finance proxies instead
config["tool_vendors"] = {
    "get_global_news": "google"  # Comprehensive but slower
}

ta = TradingAgentsGraph(config=config)
_, decision = ta.propagate("AAPL", "2024-05-10")
```

## Future Improvements

Consider these alternative free news sources for global news:
- **NewsAPI.org** (free tier: 100 requests/day)
- **Finnhub** (free tier: 60 requests/minute)
- **Alpha Vantage** (if you have an API key)

See `YFINANCE_NEWS_UPDATE.md` for more alternatives.

---

**Bottom Line:** Yahoo Finance is excellent for ticker-specific news. For comprehensive global market news, consider using Google as a fallback or exploring other news APIs.

