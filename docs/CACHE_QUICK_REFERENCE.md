# Cache System Quick Reference

## Quick Commands

### Check Cache Status
```bash
python -m tradingagents.utils.cache_monitor --health
```

### View Statistics
```bash
python -m tradingagents.utils.cache_monitor --stats
```

### Clear Cache
```bash
# Clear all
python -m tradingagents.utils.cache_monitor --clear

# Clear specific symbol
python -m tradingagents.utils.cache_monitor --clear --pattern "AAPL*"
```

### Test Cache
```bash
python -m tradingagents.utils.cache_monitor --test
```

## Redis Setup (Docker)

### Start Redis
```bash
docker run -d --name tradingagents-redis -p 6379:6379 redis:7-alpine
```

### Check Redis Status
```bash
docker ps | grep redis
docker logs tradingagents-redis
```

### Enable Redis
```bash
# Edit .env
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Stop/Start Redis
```bash
docker stop tradingagents-redis
docker start tradingagents-redis
```

## Configuration

### .env Quick Settings

**File Cache Only** (Default):
```bash
REDIS_ENABLED=false
FILE_CACHE_ENABLED=true
```

**Redis + File** (High Performance):
```bash
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
FILE_CACHE_ENABLED=true
```

### TTL Overrides

```bash
# Override specific TTLs (in seconds)
CACHE_TTL_STOCK_QUOTE=60        # 1 minute
CACHE_TTL_HISTORICAL_DATA=3600  # 1 hour
CACHE_TTL_FUNDAMENTALS=86400    # 24 hours
CACHE_TTL_NEWS=1800            # 30 minutes
```

## Programmatic Usage

### Get Cache Instance
```python
from tradingagents.dataflows.cache import get_cache

cache = get_cache()
```

### Get from Cache
```python
data = cache.get('stock_quote', symbol='AAPL')

if data is None:
    # Cache miss - fetch from API
    data = fetch_from_api('AAPL')
    cache.set('stock_quote', data, symbol='AAPL')
```

### Cache Statistics
```python
# Get stats dict
stats = cache.get_stats()

# Print formatted
cache.print_stats()
```

### Clear Cache
```python
# Clear all
cache.clear_pattern('*')

# Clear specific
cache.delete('stock_quote', symbol='AAPL')
```

## Cache Directories

All in project root:

```
cache_data/           # File cache
├── stock_quotes/     # Real-time quotes
├── historical_data/  # OHLCV data
├── fundamentals/     # Balance sheets, etc.
├── news/            # News articles
├── indicators/      # Technical indicators
└── _metadata/       # Cache metadata

chroma_db/           # Vector DB storage
data/                # Analysis results
logs/                # Application logs
```

## Common Issues

### Redis Connection Failed
```bash
# Check if running
docker ps | grep redis

# Start if not running
docker start tradingagents-redis

# Or create new
docker run -d --name tradingagents-redis -p 6379:6379 redis:7-alpine
```

**Note**: System works fine without Redis (uses file cache)!

### Cache Too Large
```bash
# Clear expired entries
python -m tradingagents.utils.cache_monitor --clear

# Or delete all
rm -rf cache_data/
```

### Permission Errors
```bash
# Fix permissions
chmod -R u+rw cache_data/
```

## Default TTL Values

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| Stock Quote | 1 min | Real-time |
| Historical Data | 1 hour | Intraday stability |
| Indicators | 1 hour | Calculated from historical |
| Fundamentals | 24 hours | Quarterly updates |
| News | 30 min | Frequent updates |
| Global News | 1 hour | Less time-sensitive |

## Performance Metrics

### Expected Hit Rates

- **First run**: 0% (building cache)
- **Second run**: 70-90% (typical)
- **Production**: 80-95% (optimal)

### Response Times

- **Redis hit**: < 1ms
- **File hit**: 5-20ms
- **API call**: 500-2000ms

### Cache Size Estimates

- **Stock quote**: ~1 KB per symbol
- **Historical data**: ~50 KB per symbol
- **Fundamentals**: ~10 KB per symbol
- **News**: ~5 KB per article

## Monitoring

### Health Check Output
```
🔴 Redis: ✅ Healthy
   Keys: 85
   Memory: 2.5MB

📁 File Cache: ✅ Healthy
   Entries: 45
   Size: 15.3 MB

🎯 Overall Hit Rate: 80.0%
```

### Statistics Output
```
📊 Overall:
  Total Requests: 150
  Total Hits: 120
  Total Misses: 30
  Hit Rate: 80.0%
```

## Best Practices

1. **Enable Redis** for production (50x+ faster)
2. **Monitor hit rates** regularly (target 70%+)
3. **Clear cache** after major data changes
4. **Backup** important analysis results
5. **Set TTLs** appropriate for your use case

## Documentation

- **Full Guide**: `docs/PHASE1_CACHE_INTEGRATION.md`
- **Architecture**: `docs/CACHE_ARCHITECTURE.md`
- **Configuration**: `env.example`

## Support

Enable debug logging:
```bash
# In .env
LOG_LEVEL=DEBUG
```

Run full diagnostic:
```bash
python -m tradingagents.utils.cache_monitor --health --verbose
```

