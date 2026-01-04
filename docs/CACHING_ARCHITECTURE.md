# TradingAgents Caching Architecture

## Overview

TradingAgents uses a multi-tier caching strategy to optimize performance and reduce API calls:

```
┌─────────────────────────────────────────────────────────────┐
│                    CACHING LAYERS                           │
├─────────────────────────────────────────────────────────────┤
│ 1. In-Memory Cache (L1) - Fastest                          │
│    └─ Provider classes: yfinance, alpha_vantage, google    │
│                                                             │
│ 2. File System Cache (L2) - Persistent                     │
│    └─ CSV files: Historical OHLCV data                     │
│                                                             │
│ 3. Vector Database (L3) - Semantic Memory                  │
│    └─ ChromaDB: Agent memory & embeddings                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer 1: In-Memory Cache

### Location
`tradingagents/dataflows/providers/us/*.py`

### Implementation
Each provider class maintains an in-memory dictionary:

```python
class YahooFinanceProvider:
    def __init__(self, cache_ttl: int = 3600):
        self._cache: Dict[str, tuple[Any, float]] = {}
        self.cache_ttl = cache_ttl  # 1 hour default
```

### Cached Data
- Stock quotes
- Historical price data
- Company information
- Fundamental data
- News articles

### TTL Configuration
```python
# dataflows/data_source_manager.py
'yfinance': {
    'enabled': True,
    'cache_ttl': 3600  # 1 hour
}
```

### Pros & Cons
✅ **Pros:**
- Extremely fast (no I/O)
- No serialization overhead
- Automatic cleanup on expiry

❌ **Cons:**
- Lost on process restart
- Not shared between processes
- Limited by available memory

---

## Layer 2: CSV File Cache

### Location
`tradingagents/dataflows/data_cache/`

### Configuration
```python
# default_config.py
"data_cache_dir": "tradingagents/dataflows/data_cache"
```

### File Format
```
{symbol}-YFin-data-{start_date}-{end_date}.csv
Example: AAPL-YFin-data-2010-01-01-2025-01-03.csv
```

### Cached Data
- Historical OHLCV data (15 years)
- Technical indicator calculations
- Stock statistics

### Implementation
```python
# y_finance.py & stockstats_utils.py
data_file = os.path.join(
    config["data_cache_dir"],
    f"{symbol}-YFin-data-{start_date}-{end_date}.csv"
)

if os.path.exists(data_file):
    data = pd.read_csv(data_file)
else:
    data = yf.download(symbol, start, end)
    data.to_csv(data_file)
```

### Expiration
- **No automatic expiration**
- Files persist indefinitely
- Manual cleanup required

### Pros & Cons
✅ **Pros:**
- Persistent across restarts
- Fast for large datasets
- Reduces API load significantly

❌ **Cons:**
- Disk space usage
- No automatic invalidation
- Stale data possible

---

## Layer 3: ChromaDB Vector Database

### Location
`chroma_db/` (project root)

### Purpose
Stores agent memory as vector embeddings for semantic retrieval.

### Collections
- `bull_memory`
- `bear_memory`
- `trader_memory`
- `invest_judge_memory`
- `risk_manager_memory`

### Implementation
```python
# agents/utils/memory.py
chroma_path = os.path.join(config["project_dir"], "chroma_db")
self.chroma_client = chromadb.PersistentClient(
    path=chroma_path,
    settings=Settings(allow_reset=True)
)
```

### Stored Data
- Past trading situations
- Investment recommendations
- Decision outcomes
- Similarity scores

### Persistence
- **Fully persistent** SQLite database
- Survives process restarts
- Enables learning from history

### Pros & Cons
✅ **Pros:**
- Semantic similarity search
- Long-term memory
- Enables agent learning

❌ **Cons:**
- Disk I/O overhead
- Requires embeddings API calls
- Not for transient data

---

## Cache Flow Examples

### Example 1: Getting Stock Quote

```
1. Tool called: get_stock_data("AAPL", "2025-01-01", "2025-01-03")
   ↓
2. Check L1 (In-Memory): Key = "quote_AAPL"
   ├─ HIT (< 1 hour old) → Return immediately ✅
   └─ MISS → Continue to step 3
   ↓
3. Check L2 (CSV): File = AAPL-YFin-data-2010-01-01-2025-01-03.csv
   ├─ EXISTS → Load from CSV ✅
   └─ NOT FOUND → Continue to step 4
   ↓
4. Fetch from Yahoo Finance API
   ↓
5. Store in L1 cache (memory) + L2 cache (CSV)
   ↓
6. Return data
```

### Example 2: Agent Retrieving Memory

```
1. Agent needs similar past situations
   ↓
2. Query ChromaDB (L3): "High volatility tech sector..."
   ↓
3. Generate embedding (OpenAI API call)
   ↓
4. Vector similarity search in ChromaDB
   ↓
5. Return top N matches with recommendations
```

---

## Cache Directories Summary

| Directory | Purpose | Type | Expiry | Size |
|-----------|---------|------|--------|------|
| `dataflows/data_cache/` | Historical CSV data | File | Never | ~100MB |
| `dataflows/cache/` | Reserved (unused) | - | N/A | Empty |
| `chroma_db/` | Agent memory vectors | SQLite | Never | ~50MB |
| (In-memory) | API responses | RAM | 1 hour | ~10MB |

---

## Configuration

### Recommended TTL by Data Type

```python
CACHE_CONFIG = {
    "stock_quote": 60,          # 1 minute (real-time)
    "historical_data": 3600,    # 1 hour (intraday)
    "fundamentals": 86400,      # 24 hours (daily)
    "news": 1800,               # 30 minutes
    "indicators": 3600,         # 1 hour
}
```

### Environment Variables

None currently used for caching. Configuration is in:
- `tradingagents/default_config.py`
- `tradingagents/dataflows/data_source_manager.py`

---

## Maintenance

### Clearing Caches

**In-Memory Cache:**
```bash
# Automatically cleared on process restart
```

**CSV Cache:**
```bash
rm -rf tradingagents/dataflows/data_cache/*.csv
```

**ChromaDB:**
```bash
rm -rf chroma_db/
```

**All Caches:**
```bash
# Full cache reset
rm -rf tradingagents/dataflows/data_cache/*.csv
rm -rf chroma_db/
# Restart process to clear in-memory cache
```

### Monitoring Cache Usage

```bash
# Check CSV cache size
du -sh tradingagents/dataflows/data_cache/

# Check ChromaDB size
du -sh chroma_db/

# List cached symbols
ls tradingagents/dataflows/data_cache/ | grep -oP '^\w+' | sort -u
```

---

## Future Enhancements

### Planned Features

1. **Redis Integration** (Phase 1 - CN feature)
   - Multi-process cache sharing
   - Pub/sub for cache invalidation
   - Production-ready scaling

2. **MongoDB Caching** (Phase 1 - CN feature)
   - Long-term historical data
   - Advanced querying
   - Replication support

3. **Smart Invalidation**
   - Market hours awareness
   - Event-based invalidation
   - Configurable staleness

4. **Cache Warming**
   - Pre-fetch popular symbols
   - Background refresh
   - Predictive caching

### TradingAgents-CN Improvements

The CN fork adds:
- `IntegratedCacheManager` class
- File-based JSON cache with MD5 keys
- TTL per market type (US vs China)
- Automatic fallback chain

---

## Troubleshooting

### Problem: Stale data

**Symptoms:** Analysis using outdated prices

**Solution:**
```bash
# Clear CSV cache
rm tradingagents/dataflows/data_cache/*-YFin-data-*.csv
```

### Problem: Out of memory

**Symptoms:** Process crashes during long sessions

**Solution:**
- Reduce `cache_ttl` values
- Restart process periodically
- Use Redis for large deployments

### Problem: ChromaDB errors

**Symptoms:** `Collection already exists` or similar

**Solution:**
```bash
# Reset ChromaDB
rm -rf chroma_db/
# Memory.py uses get_or_create, so it will recreate
```

---

## Best Practices

1. ✅ **Match TTL to data freshness needs**
   - Real-time data: 1-5 minutes
   - Fundamentals: Hours to days

2. ✅ **Monitor disk usage**
   - Set up alerts for cache size
   - Implement cleanup jobs

3. ✅ **Use appropriate cache layer**
   - Transient → In-memory
   - Historical → CSV
   - Semantic → ChromaDB

4. ✅ **Handle cache misses gracefully**
   - Always have fallback to API
   - Log cache performance metrics

5. ❌ **Don't cache user-specific data in shared caches**
   - Use session-based keys
   - Separate by user context

---

## Related Files

- `tradingagents/agents/utils/memory.py` - ChromaDB memory implementation
- `tradingagents/dataflows/providers/us/*.py` - In-memory cache providers
- `tradingagents/dataflows/y_finance.py` - CSV cache for yfinance data
- `tradingagents/dataflows/stockstats_utils.py` - CSV cache for indicators
- `tradingagents/default_config.py` - Cache directory configuration
- `tradingagents/dataflows/data_source_manager.py` - Provider cache TTL config

---

**Last Updated:** January 3, 2025

