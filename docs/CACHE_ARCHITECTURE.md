# Cache System Architecture

## System Design

### Overview

TradingAgents implements a **multi-tier caching architecture** inspired by TradingAgents-CN, designed for:

- High performance with Redis (L1 cache)
- Reliability with File (L2 cache)
- Graceful degradation when Redis unavailable
- Future MongoDB integration (Phase 2)
- WebUI support readiness

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      TradingAgents Application                   │
└─────────────────┬───────────────────────────────────────────────┘
                  │
                  ▼
        ┌──────────────────┐
        │ IntegratedCache  │
        │   (get_cache())  │
        └─────────┬────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌───────────────┐   ┌──────────────────┐
│  Redis Cache  │   │  File Cache      │
│  (L1 - Fast)  │   │  (L2 - Reliable) │
└───────┬───────┘   └────────┬─────────┘
        │                    │
        │  Cache Miss        │  Cache Miss
        └────────┬───────────┘
                 ▼
         ┌──────────────┐
         │ Data Sources │
         │ (API Vendors)│
         └──────────────┘
         ┌──────────────┐
         │ • Alpha      │
         │   Vantage    │
         │ • Yahoo      │
         │   Finance    │
         │ • Others     │
         └──────────────┘
```

## Components

### 1. IntegratedCache

**Location**: `tradingagents/dataflows/cache/integrated_cache.py`

**Purpose**: Main cache interface, coordinates between Redis and File cache.

**Key Features**:
- Automatic tier selection (Redis → File → API)
- Cache key generation with MD5 hashing
- Statistics tracking
- Graceful fallback

**Key Methods**:
```python
get(data_type, **params)      # Get from cache (multi-tier)
set(data_type, data, **params) # Set to all tiers
delete(data_type, **params)   # Delete from all tiers
clear_pattern(pattern)        # Clear matching entries
get_stats()                   # Get statistics
```

**Cache Key Generation**:
```python
def _generate_cache_key(data_type, **params):
    # Sort params for consistency
    key_parts = [data_type]
    for k, v in sorted(params.items()):
        key_parts.append(f"{k}={v}")
    
    return ":".join(key_parts)
    # Example: "stock_quote:symbol=AAPL"

def _generate_redis_key(cache_key):
    # Short hash for Redis efficiency
    hash = md5(cache_key).hexdigest()[:16]
    return f"ta:{hash}"
    # Example: "ta:a1b2c3d4e5f6g7h8"
```

### 2. RedisManager

**Location**: `tradingagents/config/redis_manager.py`

**Purpose**: Manages Redis connection with health monitoring.

**Key Features**:
- Connection pooling (configurable max connections)
- Auto-detection of Redis availability
- Health checks (ping every 30s)
- Graceful fallback if Redis unavailable
- Statistics and monitoring

**Connection Configuration**:
```python
pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=REDIS_DB,
    max_connections=10,
    decode_responses=True,
    socket_timeout=2,
    health_check_interval=30
)
```

**Health Monitoring**:
- Automatic ping checks
- Connection state tracking
- Detailed statistics (memory usage, uptime, etc.)

### 3. EnhancedFileCache

**Location**: `tradingagents/dataflows/cache/enhanced_file_cache.py`

**Purpose**: Persistent file-based cache with organized structure.

**Directory Structure**:
```
cache_data/
├── stock_quotes/        # Real-time quotes
│   ├── a1b2c3d4.pkl    # Pickled data
│   └── ...
├── historical_data/     # OHLCV data
│   └── ...
├── fundamentals/        # Balance sheets, etc.
│   └── ...
├── news/               # News articles
│   └── ...
├── indicators/         # Technical indicators
│   └── ...
└── _metadata/          # JSON metadata
    ├── a1b2c3d4.json  # Cache entry metadata
    └── ...
```

**Metadata Example**:
```json
{
  "cache_key": "stock_quote:symbol=AAPL",
  "data_type": "stock_quote",
  "cached_at": "2025-01-04T10:30:00",
  "ttl_seconds": 60,
  "data_file": "cache_data/stock_quotes/a1b2c3d4.pkl",
  "size_bytes": 1024
}
```

**Key Features**:
- Automatic TTL expiration checking
- Organized subdirectories by data type
- Metadata for each entry
- Automatic cleanup of expired entries
- Statistics tracking

### 4. CacheConfig

**Location**: `tradingagents/config/cache_config.py`

**Purpose**: Centralized cache configuration and TTL management.

**TTL Configuration**:
```python
DEFAULTS = {
    'stock_quote': 60,          # 1 minute
    'historical_data': 3600,    # 1 hour
    'fundamentals': 86400,      # 24 hours
    'news': 1800,              # 30 minutes
    # ...
}
```

**Environment Override**:
```bash
# Override in .env
CACHE_TTL_STOCK_QUOTE=120  # 2 minutes instead of default 1
```

**Configuration Methods**:
```python
get_ttl(data_type)          # Get TTL for specific type
get_all_ttls()             # Get all configured TTLs
get_redis_config()         # Get Redis settings
get_file_cache_config()    # Get file cache settings
get_mongodb_config()       # Get MongoDB settings (future)
print_config()             # Print formatted config
```

## Data Flow

### Cache Read Flow

```
1. Application calls: cache.get('stock_quote', symbol='AAPL')
   ↓
2. IntegratedCache._generate_cache_key()
   → "stock_quote:symbol=AAPL"
   ↓
3. Try Redis (L1):
   - Generate Redis key: "ta:a1b2c3d4..."
   - redis.get("ta:a1b2c3d4...")
   ↓
4a. Redis HIT:
    - Parse JSON
    - Return data
    - Log: "✅ Redis HIT: stock_quote AAPL"
    - DONE ✓
   
4b. Redis MISS:
    ↓
5. Try File Cache (L2):
   - Check: cache_data/stock_quotes/a1b2c3d4.pkl exists?
   - Read metadata: _metadata/a1b2c3d4.json
   - Check TTL expiration
   ↓
6a. File HIT & Not Expired:
    - Unpickle data
    - Promote to Redis (if available)
    - Return data
    - Log: "✅ File HIT: stock_quote AAPL"
    - DONE ✓
   
6b. File MISS or Expired:
    ↓
7. Return None
   - Application fetches from API
   - Application calls cache.set() to store result
```

### Cache Write Flow

```
1. Application calls: cache.set('stock_quote', data, symbol='AAPL')
   ↓
2. IntegratedCache._generate_cache_key()
   → "stock_quote:symbol=AAPL"
   ↓
3. Write to Redis (if available):
   - Get TTL: CacheConfig.get_ttl('stock_quote') → 60 seconds
   - Generate Redis key: "ta:a1b2c3d4..."
   - redis.setex("ta:a1b2c3d4...", 60, json.dumps(data))
   - Log: "💾 Redis SET: stock_quote AAPL"
   ↓
4. Write to File Cache:
   - Determine subdirectory: stock_quotes/
   - Pickle data: cache_data/stock_quotes/a1b2c3d4.pkl
   - Write metadata: _metadata/a1b2c3d4.json
     {
       "cache_key": "stock_quote:symbol=AAPL",
       "data_type": "stock_quote",
       "cached_at": "2025-01-04T10:30:00",
       "ttl_seconds": 60
     }
   - Log: "💾 File SET: stock_quote AAPL"
   ↓
5. Update statistics
   - Increment writes counter
   - DONE ✓
```

## Integration Points

### 1. Provider Integration

**Alpha Vantage** (`alpha_vantage_common.py`):

```python
def _make_api_request(function_name, params, use_cache=True):
    # Map function to data type
    data_type = map_function_to_type(function_name)
    
    # Try cache
    if use_cache:
        cached = cache.get(data_type, **params)
        if cached:
            return cached
    
    # Fetch from API
    response = requests.get(API_URL, params)
    
    # Cache response
    if use_cache:
        cache.set(data_type, response, **params)
    
    return response
```

**Yahoo Finance** (`y_finance.py`):

```python
def get_YFin_data_online(symbol, start_date, end_date):
    # Try cache
    cached = cache.get('historical_data', 
                       symbol=symbol, 
                       start_date=start_date, 
                       end_date=end_date)
    if cached:
        return cached
    
    # Fetch from yfinance
    data = yf.Ticker(symbol).history(start=start_date, end=end_date)
    result = format_data(data)
    
    # Cache result
    cache.set('historical_data', result,
              symbol=symbol,
              start_date=start_date,
              end_date=end_date)
    
    return result
```

### 2. Monitoring Integration

**Cache Monitor** (`utils/cache_monitor.py`):

```python
# CLI tool for cache management
python -m tradingagents.utils.cache_monitor --stats    # View stats
python -m tradingagents.utils.cache_monitor --health   # Health check
python -m tradingagents.utils.cache_monitor --clear    # Clear cache
python -m tradingagents.utils.cache_monitor --test     # Test functionality
```

**Programmatic Monitoring**:

```python
from tradingagents.dataflows.cache import get_cache

cache = get_cache()

# Get statistics
stats = cache.get_stats()
# {
#   'mode': 'High-Performance (Redis + File)',
#   'overall': {
#     'total_requests': 100,
#     'total_hits': 75,
#     'hit_rate': 75.0
#   },
#   'redis': {...},
#   'file': {...}
# }

# Print formatted stats
cache.print_stats()
```

## Performance Characteristics

### Redis Cache (L1)

- **Access Time**: < 1ms (sub-millisecond)
- **Storage**: In-memory (RAM)
- **Persistence**: Optional (AOF/RDB)
- **TTL**: Automatic expiration by Redis
- **Capacity**: Limited by RAM (typically 100MB-1GB)
- **Use Case**: Hot data, frequent access

### File Cache (L2)

- **Access Time**: 5-20ms (disk I/O)
- **Storage**: Disk (SSD/HDD)
- **Persistence**: Yes (survives restarts)
- **TTL**: Manual checking with metadata
- **Capacity**: Limited by disk (typically 1-10GB)
- **Use Case**: Warm data, backup, persistence

### API (Fallback)

- **Access Time**: 500-2000ms (network latency)
- **Storage**: External service
- **Persistence**: Vendor-dependent
- **Rate Limits**: Typically 5-500 requests/minute
- **Cost**: API credits/fees
- **Use Case**: Cache miss, fresh data

## Scalability Considerations

### Current Design (Phase 1)

**Capacity**:
- Redis: ~100MB (thousands of cache entries)
- File: ~2GB (millions of cache entries)
- Suitable for: Single user, development, small teams

**Limitations**:
- Single Redis instance (no clustering)
- Local file system (no distributed storage)
- No multi-user isolation

### Future Design (Phase 2 - MongoDB)

**Planned Enhancements**:

```
┌─────────────────────────────────────────────┐
│         IntegratedCache (Enhanced)          │
└──────┬──────────────────────────────────────┘
       │
   ┌───┴───┬────────────┬──────────────┐
   │       │            │              │
   ▼       ▼            ▼              ▼
Redis   MongoDB    File Cache     ChromaDB
(L1)    (L1.5)      (L2)          (Vector)
Fast    Persist    Backup         Memory
```

**MongoDB Benefits**:
- **Persistent storage** for analysis results
- **Multi-user support** with per-user caches
- **Query capabilities** for analytics
- **Distributed storage** with sharding
- **WebUI integration** ready

**Configuration** (ready but disabled):
```python
# Already in CacheConfig.get_mongodb_config()
MONGODB_ENABLED=false  # Enable in Phase 2
MONGODB_HOST=localhost
MONGODB_DATABASE=tradingagents
```

### WebUI Readiness

The cache system is designed for WebUI integration:

**REST API Endpoints** (future):
```python
GET  /api/cache/stats          # Get statistics
POST /api/cache/clear          # Clear cache
GET  /api/cache/health         # Health check
GET  /api/cache/entries        # List cache entries
DEL  /api/cache/entries/:key   # Delete specific entry
```

**Multi-User Support**:
```python
# User-isolated cache keys
cache_key = f"user:{user_id}:{data_type}:{params}"
# Example: "user:123:stock_quote:symbol=AAPL"
```

**Real-Time Monitoring**:
- WebSocket for live statistics
- Cache hit/miss metrics per user
- Performance dashboards

## Error Handling & Resilience

### Redis Failure Scenarios

**Scenario 1: Redis Unavailable at Startup**
```
1. RedisManager attempts connection
2. Connection fails (Redis not running)
3. Manager sets available=False
4. IntegratedCache uses File cache only
5. Log: "⚠️  Redis connection failed, falling back to file cache"
6. System continues normally ✓
```

**Scenario 2: Redis Fails During Operation**
```
1. IntegratedCache attempts Redis get()
2. Redis connection error
3. Catch exception, log warning
4. Fallback to File cache
5. Log: "⚠️  Redis error, using file cache"
6. System continues normally ✓
```

**Scenario 3: Redis Connection Lost**
```
1. Health check (every 30s) fails
2. Manager sets available=False
3. Future requests skip Redis
4. System continues with File cache ✓
```

### File Cache Failure Scenarios

**Scenario 1: Corrupted Cache File**
```
1. EnhancedFileCache attempts unpickle
2. Unpickle fails (corrupted data)
3. Catch exception, log error
4. Delete corrupted files (data + metadata)
5. Return None (cache miss)
6. Application fetches fresh data
7. Cache rebuilt ✓
```

**Scenario 2: Disk Full**
```
1. EnhancedFileCache attempts write
2. Write fails (disk full)
3. Catch exception, log error
4. Return False (cache write failed)
5. Application continues (data in memory)
6. Alert admin to free disk space
```

**Scenario 3: Permission Error**
```
1. EnhancedFileCache attempts write
2. Permission denied
3. Log error with solution
4. Return False
5. Application continues ✓
```

### Graceful Degradation

The system maintains functionality through multiple failure modes:

```
Both Working     → High-Performance Mode (Redis + File)
Redis Down       → Standard Mode (File only)
File Error       → Reduced Mode (Redis only, no persistence)
Both Down        → Direct API Mode (no caching)
```

**All modes allow the application to function!**

## Testing Strategy

### Unit Tests

**Cache Functionality**:
```python
def test_cache_set_get():
    cache = get_cache()
    cache.set('test', {'value': 123}, key='test1')
    result = cache.get('test', key='test1')
    assert result == {'value': 123}

def test_cache_expiration():
    # Set with 1-second TTL
    cache.set('test', data, ttl=1)
    time.sleep(2)
    result = cache.get('test')
    assert result is None  # Expired
```

**Fallback Behavior**:
```python
def test_redis_fallback():
    # Simulate Redis failure
    cache.redis = None
    cache.set('test', data)
    result = cache.get('test')
    # Should still work via file cache
    assert result == data
```

### Integration Tests

**Provider Integration**:
```python
def test_alpha_vantage_caching():
    # First call - cache miss
    data1 = get_alpha_vantage_stock('AAPL', ...)
    assert 'api_call' in logs
    
    # Second call - cache hit
    data2 = get_alpha_vantage_stock('AAPL', ...)
    assert data1 == data2
    assert 'cache hit' in logs
```

### Manual Testing

**Test Script**:
```bash
# Full test suite
python -m tradingagents.utils.cache_monitor --test

# Output includes:
# 1. SET and GET test
# 2. Cache MISS test
# 3. DELETE test
# 4. Final statistics
```

## Summary

**Key Design Principles**:
1. ✅ **Graceful Degradation**: Works with or without Redis
2. ✅ **Separation of Concerns**: Clear component boundaries
3. ✅ **Extensibility**: MongoDB-ready, WebUI-ready
4. ✅ **Observability**: Comprehensive statistics and logging
5. ✅ **Reliability**: Multiple fallback layers
6. ✅ **Performance**: Sub-millisecond Redis, efficient File cache
7. ✅ **Maintainability**: Root-level storage, clear organization

**Result**: Production-ready caching system that improves performance while maintaining reliability!

