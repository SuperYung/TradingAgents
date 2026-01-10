# MongoDB Integration Guide

## 🎯 Overview

TradingAgents now includes MongoDB integration for persistent storage and enhanced caching. MongoDB serves as the L3 cache tier and stores analysis results, historical data, news articles, and token usage metrics.

## 📊 Architecture

### Cache Hierarchy

```
Request
  ↓
L1: In-memory (provider-level) - Provider cache, milliseconds
  ↓ miss
L2: Redis - Hot cache, 1-5ms
  ↓ miss
L3: MongoDB - Warm persistent cache, 50-200ms
  ↓ miss
L4: File cache - Cold fallback, 10-50ms
  ↓ miss
API call - External data source, 500-2000ms
```

### MongoDB Collections

1. **analysis_reports** - Complete analysis results with decisions
2. **historical_prices** - OHLCV data from yfinance/Alpha Vantage
3. **news_articles** - News articles with sentiment analysis
4. **token_usage** - LLM token usage and cost tracking

---

## 🚀 Quick Start

### 1. Start MongoDB with Docker

```bash
# Start both Redis and MongoDB
docker-compose up -d

# Verify services are running
docker-compose ps

# Check MongoDB health
docker exec -it tradingagents-mongodb mongosh --eval "db.adminCommand('ping')"
```

### 2. Configure Environment

Create `.env` file in project root:

```bash
# Enable MongoDB
MONGODB_ENABLED=true
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=tradingagents

# Storage options
MONGODB_SAVE_ANALYSES=true
MONGODB_SAVE_NEWS=true
MONGODB_TRACK_USAGE=true
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
# This installs pymongo>=4.6.0 and motor>=3.3.0
```

### 4. Verify Setup

```bash
# Check MongoDB connection
python -m tradingagents.utils.mongo_monitor --health

# Expected output:
# ✅ MongoDB: CONNECTED AND HEALTHY
#    📊 Database: tradingagents
#    🔗 Host: localhost:27017
```

---

## 📚 Collections & Schemas

### analysis_reports

Stores complete analysis results from multi-agent system.

**Schema:**
```javascript
{
  "analysis_id": "AAPL_2026-01-10_1736524800",
  "symbol": "AAPL",
  "stock_name": "Apple Inc.",
  "market_type": "US",
  "analysis_date": "2026-01-10",
  "timestamp": ISODate("2026-01-10T14:30:00Z"),
  "status": "completed",
  
  // Configuration
  "analysts": ["Market Analyst", "Fundamentals Analyst", "News Analyst"],
  "research_depth": 1,
  "llm_config": {
    "provider": "google",
    "quick_think": "gemini-2.5-flash",
    "deep_think": "gemini-2.5-pro"
  },
  
  // Reports from each agent
  "reports": {
    "market_report": "Technical analysis shows...",
    "fundamentals_report": "Company fundamentals...",
    "news_report": "Recent news...",
    "investment_plan": "Bull/Bear debate...",
    "trader_investment_plan": "Trading strategy...",
    "final_trade_decision": "FINAL: BUY..."
  },
  
  // Structured decision
  "decision": {
    "action": "BUY",
    "confidence": 0.75,
    "reasoning": "Strong fundamentals..."
  },
  
  // Metadata
  "execution_time": 45.3,
  "session_id": "uuid",
  "source": "cli",
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

**Indexes:**
- `analysis_id` (unique)
- `symbol + timestamp`
- `analysis_date`
- `decision.action`

---

### historical_prices

Caches OHLCV data for faster queries.

**Schema:**
```javascript
{
  "symbol": "AAPL",
  "trade_date": "2026-01-10",
  "period": "1d",
  "data_source": "yfinance",
  
  // OHLCV
  "open": 180.25,
  "high": 183.50,
  "low": 179.80,
  "close": 182.75,
  "volume": 45678900,
  "adjusted_close": 182.75,
  
  // Metadata
  "created_at": ISODate("..."),
  "ttl_expires": ISODate("...")  // Auto-delete after 90 days
}
```

**Indexes:**
- `symbol + trade_date + period + data_source` (unique)
- `symbol + trade_date`
- `ttl_expires` (TTL index)

---

### news_articles

Stores news articles with sentiment.

**Schema:**
```javascript
{
  "article_id": "alphavantage_abc123",
  "symbol": "AAPL",
  "title": "Apple Reports Q1 Earnings",
  "url": "https://...",
  "published_at": ISODate("..."),
  "source": "Reuters",
  "data_provider": "alpha_vantage",
  
  "summary": "Apple Inc. reported...",
  "content": "Full article text...",
  
  "sentiment": {
    "score": 0.85,
    "label": "positive"
  },
  
  "topics": ["earnings", "technology"],
  "ttl_expires": ISODate("...")  // Auto-delete after 30 days
}
```

**Indexes:**
- `article_id` (unique)
- `symbol + published_at`
- `topics`
- `ttl_expires` (TTL index)

---

### token_usage

Tracks LLM usage and costs.

**Schema:**
```javascript
{
  "timestamp": ISODate("..."),
  "analysis_id": "AAPL_2026-01-10_...",
  "symbol": "AAPL",
  "agent": "Market Analyst",
  
  "provider": "openai",
  "model": "gpt-4",
  
  "prompt_tokens": 1500,
  "completion_tokens": 800,
  "total_tokens": 2300,
  
  "prompt_cost": 0.045,
  "completion_cost": 0.048,
  "total_cost": 0.093
}
```

**Indexes:**
- `timestamp`
- `analysis_id`
- `provider + model + timestamp`

---

## 🔧 Configuration

### Environment Variables

```bash
# Core Settings
MONGODB_ENABLED=true              # Enable/disable MongoDB
MONGODB_HOST=localhost            # MongoDB host
MONGODB_PORT=27017                # MongoDB port
MONGODB_DATABASE=tradingagents    # Database name

# Authentication (optional)
MONGODB_USERNAME=                 # Leave empty for no auth
MONGODB_PASSWORD=
MONGODB_AUTH_SOURCE=admin

# Connection Pool
MONGO_MAX_CONNECTIONS=50          # Maximum connections
MONGO_MIN_CONNECTIONS=5           # Minimum connections

# Timeouts (milliseconds)
MONGO_CONNECT_TIMEOUT_MS=10000    # Connection timeout
MONGO_SOCKET_TIMEOUT_MS=20000     # Socket timeout
MONGO_SERVER_SELECTION_TIMEOUT_MS=5000  # Server selection

# Storage Options
MONGODB_SAVE_ANALYSES=true        # Save analysis results
MONGODB_SAVE_NEWS=true            # Save news articles
MONGODB_TRACK_USAGE=true          # Track token usage

# TTL Settings (days)
MONGODB_NEWS_TTL_DAYS=30          # News auto-delete after 30 days
MONGODB_HISTORICAL_TTL_DAYS=90    # Historical data after 90 days
```

---

## 🛠️ MongoDB Monitor Utility

Command-line tool to inspect and manage MongoDB.

### Check Health

```bash
python -m tradingagents.utils.mongo_monitor --health
```

Output:
```
==================================================================
  MongoDB Health Check
==================================================================
✅ MongoDB: CONNECTED AND HEALTHY
   📊 Database: tradingagents
   🔗 Host: localhost:27017
   🏊 Pool: 5-50 connections
   ⏱️  Timeouts: connect=10000ms, socket=20000ms
```

### Show Statistics

```bash
python -m tradingagents.utils.mongo_monitor --stats
```

Output:
```
==================================================================
  MongoDB Statistics
==================================================================

📊 Analysis Reports:
   Total Analyses: 42
   By Status: {'completed': 40, 'failed': 2}
   By Action: {'BUY': 15, 'SELL': 10, 'HOLD': 15}

📈 Historical Prices:
   Total Records: 12,450
   Unique Symbols: 25
   Sample Symbols: AAPL, MSFT, GOOGL, TSLA, AMZN

📰 News Articles:
   Total Articles: 234
   Unique Symbols: 18
   Recent (7 days): 45

💰 Token Usage:
   Total Records: 156
   Unique Providers: 2
   Providers: openai, google
```

### Show Recent Analyses

```bash
python -m tradingagents.utils.mongo_monitor --recent 5
```

### Token Usage Summary

```bash
python -m tradingagents.utils.mongo_monitor --usage 7
```

Output:
```
📊 Overall:
   Total Records: 42
   Total Tokens: 125,430
   Total Cost: $3.45

💳 By Provider:
   openai:
     Calls: 25
     Tokens: 75,000
     Cost: $2.25
   google:
     Calls: 17
     Tokens: 50,430
     Cost: $1.20
```

### Clean Old Data

```bash
# Delete data older than 90 days
python -m tradingagents.utils.mongo_monitor --clean 90

# Delete only news older than 30 days
python -m tradingagents.utils.mongo_monitor --clean 30 --type news
```

---

## 📝 Usage Examples

### Save Analysis Results (Automatic)

Analysis results are automatically saved to MongoDB when:
1. `MONGODB_ENABLED=true`
2. `MONGODB_SAVE_ANALYSES=true`
3. Analysis completes successfully

```python
# In trading_graph.py (already integrated)
# MongoDB save happens automatically after analysis
```

### Query Analysis Results

```python
from tradingagents.dataflows.mongodb import AnalysisRepository

repo = AnalysisRepository()

# Get specific analysis
analysis = repo.get_analysis_by_id("AAPL_2026-01-10_1736524800")

# Get recent analyses for symbol
analyses = repo.get_analyses_by_symbol("AAPL", limit=10)

# Get analyses by date range
analyses = repo.get_analyses_by_date_range("2026-01-01", "2026-01-31")
```

### Cache Historical Data

```python
from tradingagents.dataflows.mongodb import HistoricalRepository
import pandas as pd

repo = HistoricalRepository()

# Save historical data (automatic via integrated cache)
df = pd.DataFrame(...)  # OHLCV data
repo.save_historical_data("AAPL", df, period="1d", data_source="yfinance")

# Retrieve from MongoDB cache
df = repo.get_historical_data("AAPL", "2026-01-01", "2026-01-31")
```

### Track Token Usage

```python
from tradingagents.dataflows.mongodb import UsageRepository

repo = UsageRepository()

# Log usage (automatic when integrated)
usage_data = {
    "analysis_id": "AAPL_...",
    "symbol": "AAPL",
    "agent": "Market Analyst",
    "provider": "openai",
    "model": "gpt-4",
    "total_tokens": 2300,
    "total_cost": 0.093
}
repo.log_usage(usage_data)

# Get usage summary
summary = repo.get_usage_summary(days=7)
print(f"Total cost last 7 days: ${summary['total_cost']}")
```

---

## 🐳 Docker Setup

### docker-compose.yml

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: tradingagents-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  mongodb:
    image: mongo:7
    container_name: tradingagents-mongodb
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_DATABASE: tradingagents
    volumes:
      - mongodb_data:/data/db
      - ./scripts/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro

volumes:
  redis_data:
  mongodb_data:
```

### Common Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f mongodb

# Stop services
docker-compose down

# Stop and remove volumes (delete all data)
docker-compose down -v

# Connect to MongoDB shell
docker exec -it tradingagents-mongodb mongosh tradingagents
```

---

## 🔍 Troubleshooting

### MongoDB Not Connecting

**Problem**: Cache shows "File Only" mode

**Solutions**:
1. Check Docker is running: `docker ps`
2. Check MongoDB status: `docker-compose ps`
3. Verify `.env`: `MONGODB_ENABLED=true`
4. Test connection: `python -m tradingagents.utils.mongo_monitor --health`

### Indexes Not Created

**Problem**: Slow queries

**Solution**:
```bash
# Reinitialize MongoDB
docker-compose down
docker-compose up -d

# Or manually create indexes
docker exec -it tradingagents-mongodb mongosh tradingagents < scripts/mongo-init.js
```

### High Memory Usage

**Problem**: MongoDB using too much RAM

**Solution**:
```bash
# Clean old data
python -m tradingagents.utils.mongo_monitor --clean 30

# Or set TTL in environment
MONGODB_NEWS_TTL_DAYS=7
MONGODB_HISTORICAL_TTL_DAYS=30
```

---

## 📊 Performance Tips

### 1. Adjust Connection Pool

For high concurrency:
```bash
MONGO_MAX_CONNECTIONS=100
MONGO_MIN_CONNECTIONS=10
```

### 2. Optimize TTL Settings

Balance storage vs freshness:
```bash
# Keep less data
MONGODB_NEWS_TTL_DAYS=7
MONGODB_HISTORICAL_TTL_DAYS=30

# Keep more data
MONGODB_NEWS_TTL_DAYS=90
MONGODB_HISTORICAL_TTL_DAYS=365
```

### 3. Selective Storage

Disable features you don't need:
```bash
MONGODB_SAVE_ANALYSES=true
MONGODB_SAVE_NEWS=false      # Disable news storage
MONGODB_TRACK_USAGE=false    # Disable usage tracking
```

---

## 🎯 Next Steps

Now that MongoDB is integrated, you can:

1. **Build WebUI** - Display analysis history and results
2. **Add Analytics** - Backtest strategies using stored analyses
3. **Cost Tracking** - Monitor LLM usage and optimize costs
4. **API Endpoints** - Expose MongoDB data via REST API

---

## 📚 Related Documentation

- [Cache Architecture](./CACHE_ARCHITECTURE.md)
- [Cache Quick Reference](./CACHE_QUICK_REFERENCE.md)
- [Installation & Testing](./INSTALLATION_TESTING.md)

