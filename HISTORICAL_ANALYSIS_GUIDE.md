# Historical Analysis Guide

## Problem: Analyzing Historical Dates

When analyzing dates more than ~7 days in the past, Yahoo Finance returns no news or empty data because it only provides recent news.

## Solutions for Historical Analysis

### **Option 1: Use Google News (Slower but Historical)**

Google News scraping can retrieve historical news. Enable it for global news:

```python
from tradingagents.default_config import DEFAULT_CONFIG

config = DEFAULT_CONFIG.copy()

# Use Google for global news (has historical data)
config["tool_vendors"] = {
    "get_global_news": "google"
}

ta = TradingAgentsGraph(config=config)
_, decision = ta.propagate("AAPL", "2024-05-10")  # Historical date
```

**Trade-offs:**
- ✅ Can retrieve historical news
- ❌ Slower (30-60 seconds due to web scraping)
- ❌ Subject to rate limiting/blocking

### **Option 2: Use Current Date for Analysis**

For testing/learning purposes, use recent dates:

```python
from datetime import datetime, timedelta

# Use today or recent date
recent_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

ta = TradingAgentsGraph()
_, decision = ta.propagate("AAPL", recent_date)  # Recent date works!
```

### **Option 3: NewsAPI.org (Historical + Fast)**

NewsAPI provides historical news up to 1 month (free tier):

1. Get free API key from https://newsapi.org/
2. Implement NewsAPI integration (see example below)

```python
# Example NewsAPI integration (you would need to implement)
from newsapi import NewsApiClient

newsapi = NewsApiClient(api_key='YOUR_API_KEY')
articles = newsapi.get_everything(
    q='AAPL OR Apple',
    from_param='2024-05-01',
    to='2024-05-10',
    language='en',
    sort_by='relevancy'
)
```

### **Option 4: Local/Cached Historical Data**

For specific historical dates you frequently analyze, save news data locally:

```python
# Save news data for historical dates
import json

historical_news = {
    "2024-05-10": {
        "AAPL": "Apple announces new product...",
        "global": "Market rallies on positive jobs report..."
    }
}

# Use local data provider
config["data_vendors"]["news_data"] = "local"
```

### **Option 5: Finnhub (Historical + Free Tier)**

Finnhub provides company news with historical data:

```python
import finnhub

finnhub_client = finnhub.Client(api_key="YOUR_KEY")
news = finnhub_client.company_news('AAPL', _from="2024-05-01", to="2024-05-10")
```

**Free tier:** 60 API calls/minute

## Recommended Approach by Use Case

| Use Case | Recommended Solution | Why |
|----------|---------------------|-----|
| **Learning/Testing** | Use current date | Fast, reliable, no setup |
| **Production (recent dates)** | Yahoo Finance | Fast, unlimited, free |
| **Historical Backtesting** | Google News or NewsAPI | Has historical data |
| **Research (specific dates)** | Local cached data | Fast, deterministic |
| **Enterprise** | Paid news API | Reliable, comprehensive, historical |

## Quick Fix: Update Your Test Date

The simplest solution for immediate testing:

```python
# Instead of:
ta.propagate("AAPL", "2024-05-10")  # 7+ months ago

# Use:
from datetime import datetime
today = datetime.now().strftime("%Y-%m-%d")
ta.propagate("AAPL", today)  # Current date works!
```

## Verification

Check if news is available for your date:

```python
import yfinance as yf
from datetime import datetime

ticker = yf.Ticker("AAPL")
news = ticker.news

if news:
    print(f"✅ Found {len(news)} articles")
    latest = datetime.fromtimestamp(news[0]['providerPublishTime'])
    print(f"Latest article: {latest}")
else:
    print("❌ No news available")
```

## System Behavior

When analyzing historical dates with Yahoo Finance:

1. **Ticker news**: Returns recent news (not for the historical date)
2. **Global news**: Returns "No valid data available" message
3. **Analysis continues**: Agents use available data (fundamentals, technicals)
4. **Report quality**: Lower quality due to missing news context

---

**Bottom line:** For historical analysis beyond 7 days, switch to Google News or use current dates for testing.

