# Phase 1 Cache Integration - Installation & Testing Guide

## Prerequisites

- Python 3.9+
- pip or uv package manager
- Docker (optional, for Redis)

## Installation Steps

### 1. Install Python Dependencies

```bash
# Navigate to project root
cd /Users/YChou1/Development/MyCursor/TradingAgents

# Install all dependencies
pip install -r requirements.txt

# Or using uv (faster)
uv pip install -r requirements.txt
```

**Key new dependencies** (already in requirements.txt):
- `redis` - Redis client library

### 2. Setup Environment

```bash
# Copy environment template
cp env.example .env

# Edit .env and configure:
# - API keys (OpenAI, Alpha Vantage, etc.)
# - Cache settings (see below)
```

### 3. Optional: Setup Redis (Recommended for Production)

#### Using Docker (Recommended):

```bash
# Start Redis
docker run -d \
  --name tradingagents-redis \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7-alpine redis-server --appendonly yes

# Verify Redis is running
docker ps | grep redis
```

#### Or using local Redis:

```bash
# macOS (Homebrew)
brew install redis
brew services start redis

# Linux (apt)
sudo apt update
sudo apt install redis-server
sudo systemctl start redis

# Verify
redis-cli ping
# Should return: PONG
```

### 4. Configure Cache Settings

Edit `.env`:

**For Redis + File (High Performance)**:
```bash
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
FILE_CACHE_ENABLED=true
```

**For File Cache Only** (Default, works without Redis):
```bash
REDIS_ENABLED=false
FILE_CACHE_ENABLED=true
```

## Verification

### Quick Verification

Run the cache monitor to verify installation:

```bash
python -m tradingagents.utils.cache_monitor --health
```

**Expected output** (with Redis):
```
======================================================================
TradingAgents Cache Monitor
======================================================================

🏥 Cache Health Check
----------------------------------------------------------------------

🔴 Redis: ✅ Healthy
   Keys: 0
   Memory: 1.2MB
   Uptime: 0 days

📁 File Cache: ✅ Healthy
   Entries: 0
   Size: 0.0 MB
   Hit Rate: 0.0%

🎯 Overall:
   Mode: High-Performance (Redis + File)
   Total Requests: 0
   Overall Hit Rate: 0.0%

💡 Recommendations:
   • All systems healthy!
```

**Expected output** (without Redis):
```
🔴 Redis: ⚠️  Unavailable (using file cache)

📁 File Cache: ✅ Healthy
   ...

🎯 Overall:
   Mode: Standard (File Only)
   ...
```

### Comprehensive Testing

Run the full test suite:

```bash
# Make sure dependencies are installed
pip install -r requirements.txt

# Run Phase 1 cache tests
python3 tests/test_phase1_cache.py
```

**Expected output**:
```
======================================================================
PHASE 1 CACHE INTEGRATION TEST SUITE
======================================================================

======================================================================
TEST 1: Module Imports
======================================================================
✅ All modules imported successfully

======================================================================
TEST 2: CacheConfig
======================================================================
✅ get_ttl('stock_quote') = 60s
✅ get_all_ttls() returned 13 TTL configs
✅ Redis config: enabled=true
✅ File cache config: enabled=true

... (more tests) ...

======================================================================
TEST SUMMARY
======================================================================
✅ PASS: Module Imports
✅ PASS: CacheConfig
✅ PASS: RedisManager
✅ PASS: EnhancedFileCache
✅ PASS: IntegratedCache
✅ PASS: Provider Integration
✅ PASS: Cache Monitor

======================================================================
TOTAL: 7/7 tests passed (100.0%)
======================================================================

🎉 All tests passed! Cache integration is working correctly.
```

### Manual Testing

Test cache functionality manually:

```bash
# Test cache functionality
python -m tradingagents.utils.cache_monitor --test
```

**Expected output**:
```
======================================================================
TradingAgents Cache Monitor
======================================================================

🧪 Testing cache functionality...
----------------------------------------------------------------------

1. Testing SET and GET:
   ✅ SET: stock_quote for AAPL
   ✅ GET: Retrieved correct data

2. Testing cache MISS:
   ✅ Cache miss returned None as expected

3. Testing DELETE:
   ✅ DELETE: Entry removed successfully

4. Final Statistics:
   ...

✅ Cache testing complete!
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'redis'"

**Solution**:
```bash
pip install redis

# Or reinstall all dependencies
pip install -r requirements.txt
```

### Issue: "Redis connection failed"

**Check if Redis is running**:
```bash
# Docker
docker ps | grep redis

# Local
redis-cli ping
```

**Start Redis if not running**:
```bash
# Docker
docker start tradingagents-redis

# Or create new
docker run -d --name tradingagents-redis -p 6379:6379 redis:7-alpine

# Local (Homebrew on macOS)
brew services start redis
```

**Note**: System works fine without Redis using file cache!

### Issue: "Permission denied" on cache_data

**Solution**:
```bash
# Fix permissions
chmod -R u+rw cache_data/

# Or delete and let system recreate
rm -rf cache_data/
```

### Issue: Test failures due to missing dependencies

**Solution**:
```bash
# Make sure you're in the correct environment
# If using virtual environment:
source .venv/bin/activate  # or activate.bat on Windows

# Install all dependencies
pip install -r requirements.txt

# Verify installations
pip list | grep redis
pip list | grep requests
```

## Directory Structure After Installation

After successful installation, you should see:

```
TradingAgents/
├── cache_data/           # ✅ Created on first cache write
│   ├── stock_quotes/
│   ├── historical_data/
│   ├── fundamentals/
│   ├── news/
│   ├── indicators/
│   └── _metadata/
├── chroma_db/           # ✅ ChromaDB storage (existing)
├── .env                 # ✅ Your configuration
├── env.example          # ✅ Configuration template
├── tradingagents/
│   ├── config/          # ✅ NEW - Cache configuration
│   │   ├── redis_manager.py
│   │   ├── cache_config.py
│   │   └── __init__.py
│   ├── dataflows/
│   │   └── cache/       # ✅ NEW - Cache system
│   │       ├── integrated_cache.py
│   │       ├── enhanced_file_cache.py
│   │       └── __init__.py
│   └── utils/
│       └── cache_monitor.py  # ✅ NEW - Monitoring tool
├── docs/                # ✅ NEW - Documentation
│   ├── PHASE1_CACHE_INTEGRATION.md
│   ├── CACHE_ARCHITECTURE.md
│   └── CACHE_QUICK_REFERENCE.md
└── tests/
    └── test_phase1_cache.py  # ✅ NEW - Test suite
```

## Usage After Installation

### Running CLI with Caching

Caching is **automatic** - just use the CLI normally:

```bash
# Run CLI
python cli/main.py

# Select analysts, symbol, and date range
# Caching happens automatically!

# First run: Slower (building cache)
# Second run: Much faster (using cache)
```

### Monitoring Cache

```bash
# View statistics
python -m tradingagents.utils.cache_monitor --stats

# Check health
python -m tradingagents.utils.cache_monitor --health

# Clear cache
python -m tradingagents.utils.cache_monitor --clear
```

### Programmatic Usage

```python
from tradingagents.dataflows.cache import get_cache

# Get cache instance
cache = get_cache()

# Use cache
data = cache.get('stock_quote', symbol='AAPL')
if data is None:
    data = fetch_from_api('AAPL')
    cache.set('stock_quote', data, symbol='AAPL')
```

## Performance Expectations

### First Run (Cold Cache)
```
Analysis Time: ~30-60 seconds
API Calls: 10-20
Cache Hits: 0%
```

### Second Run (Warm Cache)
```
Analysis Time: ~1-5 seconds (10-50x faster)
API Calls: 0-2
Cache Hits: 80-95%
```

### With Redis
```
Cache Hit Response: < 1ms
File Cache Hit: 5-20ms
API Call: 500-2000ms
```

## Next Steps

1. ✅ **Verify installation**: Run health check
2. ✅ **Test functionality**: Run test suite
3. ✅ **Configure settings**: Edit .env for your needs
4. ✅ **Run analysis**: Use CLI normally
5. ✅ **Monitor performance**: Check cache stats

## Documentation

- **User Guide**: `docs/PHASE1_CACHE_INTEGRATION.md`
- **Architecture**: `docs/CACHE_ARCHITECTURE.md`
- **Quick Reference**: `docs/CACHE_QUICK_REFERENCE.md`
- **This Guide**: `docs/INSTALLATION_TESTING.md`

## Support

### Enable Debug Logging

```bash
# In .env
LOG_LEVEL=DEBUG
```

### Get Full Diagnostics

```bash
python -m tradingagents.utils.cache_monitor --health --verbose
```

### Check Logs

```bash
# View application logs
tail -f logs/tradingagents.log

# View Redis logs (Docker)
docker logs tradingagents-redis
```

## Success Checklist

- [ ] Python dependencies installed (`pip install -r requirements.txt`)
- [ ] Redis running (optional, `docker ps | grep redis`)
- [ ] `.env` file configured
- [ ] Health check passes (`python -m tradingagents.utils.cache_monitor --health`)
- [ ] Tests pass (`python3 tests/test_phase1_cache.py`)
- [ ] CLI works with caching enabled

**If all checks pass**: 🎉 **Installation successful!** You're ready to use the enhanced caching system.

