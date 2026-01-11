# News MongoDB Integration - Complete

## Overview
Implemented automatic news article saving to MongoDB when news is fetched during analysis.

## Implementation Strategy

### Approach: Interceptor Pattern
Rather than modifying every news tool, we intercept news data at the **data source level** and save it to MongoDB automatically.

### Architecture
```
News API (Alpha Vantage / OpenAI / Google)
    ↓
alpha_vantage_common._make_api_request()
    ↓
response_json (news data)
    ↓
news_saver.save_news_from_response()  ← Automatic!
    ↓
NewsRepository.save_news_batch()
    ↓
MongoDB news_articles collection
```

## Files Created/Modified

### 1. New File: `tradingagents/dataflows/news_saver.py`

**Purpose:** Parse and save news articles from various API formats

**Key Components:**

#### NewsSaver Class
```python
class NewsSaver:
    def __init__(self):
        # Only enabled if MongoDB is enabled and news saving is enabled
        self.enabled = (
            DEFAULT_CONFIG.get('mongodb_enabled') and 
            DEFAULT_CONFIG.get('mongodb_save_news')
        )
    
    def save_news_from_response(self, news_data, symbol, source):
        # Extract articles
        # Save to MongoDB
        # Return count
```

#### Format Support
- ✅ **Alpha Vantage NEWS_SENTIMENT** - Full sentiment data
- ✅ **Generic JSON** - OpenAI, Google, others
- ✅ **Article lists** - Common format

#### Article Schema
```python
{
    'title': str,
    'url': str,
    'published_at': datetime,
    'source': {
        'name': str,
        'domain': str (Alpha Vantage only),
        'api_source': str  # alpha_vantage, openai, google
    },
    'summary': str,
    'topics': [str],  # Tags, categories
    'symbols': [str],  # Related stock symbols
    'sentiment': {  # Alpha Vantage only
        'overall': str,  # Positive, Negative, Neutral
        'score': float,  # -1 to 1
        'tickers': [{...}]  # Per-ticker sentiment
    },
    'authors': [str],
    'category': str,
    'retrieved_at': datetime
}
```

### 2. Modified: `tradingagents/dataflows/alpha_vantage_common.py`

**Changes:**
```python
# Added import
from tradingagents.dataflows.news_saver import get_news_saver
news_saver = get_news_saver()

# In _make_api_request(), after caching JSON response:
if function_name == 'NEWS_SENTIMENT':
    symbol = params.get('tickers') or params.get('symbol')
    news_saver.save_news_from_response(
        response_json, 
        symbol=symbol,
        source='alpha_vantage'
    )
```

**Result:** All Alpha Vantage news requests automatically save to MongoDB!

## Configuration

### Environment Variables (.env)
```env
# Enable MongoDB
MONGODB_ENABLED=true

# Enable news saving (default: true)
MONGODB_SAVE_NEWS=true

# News TTL in days (default: 30)
MONGODB_NEWS_TTL_DAYS=30
```

### default_config.py
Already configured:
```python
"mongodb_save_news": os.getenv("MONGODB_SAVE_NEWS", "true").lower() == "true",
```

## Data Flow

### Analysis Run
```
1. News Analyst agent runs
   ↓
2. Calls get_news(ticker, start_date, end_date)
   ↓
3. Routes to Alpha Vantage provider
   ↓
4. alpha_vantage_common._make_api_request('NEWS_SENTIMENT', ...)
   ↓
5. API response received (JSON with 'feed' array)
   ↓
6. Cache.set() saves for future use
   ↓
7. news_saver.save_news_from_response() ← NEW!
   ↓
8. Extracts articles from feed
   ↓
9. Parses each article (title, url, sentiment, etc.)
   ↓
10. NewsRepository.save_news_batch()
   ↓
11. MongoDB saves to news_articles collection
```

## Alpha Vantage NEWS_SENTIMENT Format

### Example Response
```json
{
  "items": "50",
  "sentiment_score_definition": "...",
  "relevance_score_definition": "...",
  "feed": [
    {
      "title": "Apple Announces Q4 Earnings Beat",
      "url": "https://...",
      "time_published": "20240115T153000",
      "authors": ["John Doe"],
      "summary": "Apple Inc. reported...",
      "source": "Reuters",
      "source_domain": "reuters.com",
      "topics": [
        {"topic": "Earnings", "relevance_score": "1.0"}
      ],
      "overall_sentiment_score": 0.25,
      "overall_sentiment_label": "Somewhat-Bullish",
      "ticker_sentiment": [
        {
          "ticker": "AAPL",
          "relevance_score": "1.0",
          "ticker_sentiment_score": "0.3",
          "ticker_sentiment_label": "Bullish"
        }
      ]
    }
  ]
}
```

### What We Save
- **Basic Info:** title, url, published date, summary
- **Source:** Reuters, Bloomberg, CNBC, etc.
- **Sentiment:** Overall + per-ticker sentiment scores
- **Topics:** Earnings, M&A, IPO, etc.
- **Symbols:** Related tickers with relevance scores
- **Authors:** Article authors

## MongoDB Storage

### Collection: `news_articles`

### Indexes
```javascript
// Created by NewsRepository
{ "symbols": 1, "published_at": -1 }  // Query by symbol + date
{ "published_at": -1 }                 // Recent news
{ "topics": 1 }                        // Query by topics
{ "created_at": 1 }, { expireAfterSeconds: 2592000 }  // TTL: 30 days
```

### TTL (Time To Live)
- **Default:** 30 days
- **Configurable:** `MONGODB_NEWS_TTL_DAYS` in .env
- **Auto-cleanup:** MongoDB automatically deletes old news

## Usage Examples

### Query Recent News for Symbol
```python
from tradingagents.dataflows.mongodb.news_repository import NewsRepository

repo = NewsRepository()
articles = repo.get_news_by_symbol("AAPL", limit=10)

for article in articles:
    print(f"{article['title']} - {article['source']['name']}")
    print(f"Sentiment: {article.get('sentiment', {}).get('overall', 'N/A')}")
```

### Query by Date Range
```python
articles = repo.get_news_by_date_range(
    start_date="2024-01-01",
    end_date="2024-01-31",
    symbol="AAPL"
)
```

### Query by Topics
```python
articles = repo.get_news_by_topics(
    topics=["Earnings", "M&A"],
    limit=20
)
```

## Testing

### 1. Run Analysis with News
```bash
python -m cli.main
# Select News Analyst when prompted
```

### 2. Check Logs
```bash
grep "news_saver\|NewsRepository" logs/tradingagents.log
```

Expected:
```
📰 News saver initialized (MongoDB enabled)
🌐 API Request: NEWS_SENTIMENT AAPL
📰 Saving 50 news articles to MongoDB...
✅ Saved 50/50 news articles to MongoDB
```

### 3. Check MongoDB
```bash
python -m tradingagents.utils.mongo_monitor --stats
```

Expected:
```
📰 News Articles:
   Total Articles: 50  ✅
   Unique Symbols: 5
   Recent (7 days): 50
```

### 4. View Recent News
```bash
python -m tradingagents.utils.mongo_monitor --news
```

## Extending to Other Sources

### For OpenAI News
Update `openai.py` similarly:
```python
from tradingagents.dataflows.news_saver import get_news_saver
news_saver = get_news_saver()

def get_global_news_openai(...):
    # ... fetch news ...
    news_saver.save_news_from_response(news_data, source='openai')
    return news_data
```

### For Google News
Same pattern in google provider.

### Custom Formats
NewsSaver already handles:
- Alpha Vantage format (with `feed` key)
- Generic list format
- Generic dict with `articles` key

For new formats, add parsing logic to `_extract_articles()`.

## Benefits

### ✅ Automatic
- No manual save calls needed
- Works wherever news is fetched
- Consistent across all analysts

### ✅ Comprehensive
- Saves all article metadata
- Includes sentiment data (when available)
- Tracks sources and topics

### ✅ Queryable
- Find news by symbol
- Filter by date range
- Search by topics/categories
- Analyze sentiment trends

### ✅ Performant
- Non-blocking saves
- Batch operations
- Indexed queries
- Auto-expiring (TTL)

## Limitations & Future Work

### Current Limitations
1. **Only Alpha Vantage integrated** - Need to add OpenAI, Google
2. **No deduplication** - Same article from multiple sources saved multiple times
3. **No full-text search** - Would need MongoDB text index or external search

### Future Enhancements
1. **Article deduplication** - Hash URLs or titles
2. **Sentiment analysis** - Add our own sentiment if not provided
3. **Entity extraction** - Extract companies, people, places
4. **Text search** - Add MongoDB text index for keyword search
5. **News aggregation** - Deduplicate and aggregate from multiple sources
6. **Relevance scoring** - Rank articles by relevance to portfolio

## Date Implemented
2026-01-10

## Related Documentation
- [MongoDB Integration](./MONGODB_COMPLETE.md)
- [NewsRepository API](../tradingagents/dataflows/mongodb/news_repository.py)
- [Alpha Vantage News API](https://www.alphavantage.co/documentation/#news-sentiment)

