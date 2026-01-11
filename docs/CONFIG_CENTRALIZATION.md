# Configuration Centralization Refactoring

## Overview
Refactored the codebase to use a **centralized configuration pattern** where all configuration is loaded and managed through `default_config.py`, eliminating duplication and inconsistency.

## Problem (Before)

### Inconsistent Configuration Loading
1. **Redis Manager** - Loaded its own `.env` and used `os.getenv()` directly
2. **MongoDB Manager** - Loaded its own `.env` and used `os.getenv()` directly
3. **Default Config** - Also had MongoDB config (duplicate!)
4. Result: **Three different places** loading config independently

### Issues
- ❌ Configuration duplicated between `DEFAULT_CONFIG` and manager classes
- ❌ Multiple `load_dotenv()` calls scattered across files
- ❌ Inconsistent: Redis config not in `DEFAULT_CONFIG`, but MongoDB was
- ❌ Hard to see all config in one place
- ❌ Config loading order could cause issues

## Solution (After)

### Centralized Configuration Pattern

```
┌─────────────────────────────────────────────┐
│          default_config.py                  │
│  ┌───────────────────────────────────────┐  │
│  │  1. Load .env file (once)             │  │
│  │  2. Read all environment variables    │  │
│  │  3. Build DEFAULT_CONFIG dictionary   │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                    ↓
        Single Source of Truth
                    ↓
    ┌───────────────┴───────────────┐
    ↓                               ↓
┌──────────────┐            ┌──────────────┐
│ RedisManager │            │MongoDBManager│
│              │            │              │
│ Uses:        │            │ Uses:        │
│ DEFAULT_     │            │ DEFAULT_     │
│ CONFIG       │            │ CONFIG       │
└──────────────┘            └──────────────┘
```

## Changes Made

### 1. default_config.py
**Added Redis configuration:**
```python
# Redis configuration (L2 Cache)
"redis_enabled": os.getenv("REDIS_ENABLED", "false").lower() == "true",
"redis_host": os.getenv("REDIS_HOST", "localhost"),
"redis_port": int(os.getenv("REDIS_PORT", "6379")),
"redis_db": int(os.getenv("REDIS_DB", "0")),
"redis_password": os.getenv("REDIS_PASSWORD", ""),
```

**Updated MongoDB section comment:**
```python
# MongoDB configuration (L3 Cache + Persistent Storage)
```

### 2. redis_manager.py
**Before:**
```python
# Auto-load .env file
from dotenv import load_dotenv
load_dotenv(...)

class RedisManager:
    def __init__(self):
        self.enabled = os.getenv("REDIS_ENABLED", "false")
        self.host = os.getenv("REDIS_HOST", "localhost")
        # ... more os.getenv() calls
```

**After:**
```python
from tradingagents.default_config import DEFAULT_CONFIG

class RedisManager:
    def __init__(self):
        self.enabled = DEFAULT_CONFIG.get('redis_enabled', False)
        self.host = DEFAULT_CONFIG.get('redis_host', 'localhost')
        # ... uses DEFAULT_CONFIG throughout
```

**Changes:**
- ✅ Removed `load_dotenv()` call (now in default_config.py)
- ✅ Removed all `os.getenv()` calls
- ✅ Now reads from `DEFAULT_CONFIG` dictionary
- ✅ Removed `_parse_bool()` helper (boolean parsing in default_config)

### 3. mongodb_manager.py
**Before:**
```python
# Load environment variables
from dotenv import load_dotenv
load_dotenv(...)

class MongoDBManager:
    def __init__(self):
        self.enabled = os.getenv('MONGODB_ENABLED', 'false').lower() == 'true'
        self.host = os.getenv('MONGODB_HOST', 'localhost')
        # ... more os.getenv() calls
```

**After:**
```python
from tradingagents.default_config import DEFAULT_CONFIG

class MongoDBManager:
    def __init__(self):
        self.enabled = DEFAULT_CONFIG.get('mongodb_enabled', False)
        self.host = DEFAULT_CONFIG.get('mongodb_host', 'localhost')
        # ... uses DEFAULT_CONFIG for main config
        # Still uses os.getenv() for optional auth settings
```

**Changes:**
- ✅ Removed `load_dotenv()` block
- ✅ Removed most `os.getenv()` calls
- ✅ Now reads from `DEFAULT_CONFIG` dictionary
- ⚠️ Kept `os.getenv()` for optional auth settings (username/password)

## Benefits

### 1. Single Source of Truth
```python
# Want to see all config? Just look at default_config.py!
from tradingagents.default_config import DEFAULT_CONFIG
print(DEFAULT_CONFIG)  # Everything is here
```

### 2. Consistent Pattern
```python
# Every module uses the same pattern
from tradingagents.default_config import DEFAULT_CONFIG
value = DEFAULT_CONFIG.get('setting_name', default)
```

### 3. No Duplication
- Redis config: ✅ In DEFAULT_CONFIG only
- MongoDB config: ✅ In DEFAULT_CONFIG only
- `.env` loading: ✅ Once in default_config.py

### 4. Easier Testing
```python
# Mock config in tests by patching one place
with patch('tradingagents.default_config.DEFAULT_CONFIG', mock_config):
    # All modules use mocked config
```

### 5. Better Performance
- `.env` file loaded **once** on first import
- Config dictionary built once, reused everywhere
- No redundant file I/O

## Configuration Hierarchy

### Load Order:
```
1. default_config.py imports
   ↓
2. load_dotenv() reads .env file
   ↓
3. os.getenv() reads environment variables
   ↓
4. DEFAULT_CONFIG dict created with all settings
   ↓
5. Managers import DEFAULT_CONFIG (already loaded)
```

### Priority (highest to lowest):
1. **System environment variables** (set in shell/Docker)
2. **`.env` file** (project-specific overrides)
3. **Hard-coded defaults** in `os.getenv(..., "default")`

## All Configuration in DEFAULT_CONFIG

### Application Settings
- `project_dir`, `results_dir`, `data_dir`
- `llm_provider`, `deep_think_llm`, `quick_think_llm`
- `max_debate_rounds`, `max_risk_discuss_rounds`

### Redis (L2 Cache)
- `redis_enabled`, `redis_host`, `redis_port`
- `redis_db`, `redis_password`

### MongoDB (L3 Cache + Storage)
- `mongodb_enabled`, `mongodb_host`, `mongodb_port`
- `mongodb_database`
- `mongodb_save_analyses`, `mongodb_save_news`, `mongodb_track_usage`

### Data Vendors
- `data_vendors` dict (per-category defaults)
- `tool_vendors` dict (per-tool overrides)

## Files Modified

1. ✅ `tradingagents/default_config.py`
   - Added Redis configuration section
   - Updated comments for clarity

2. ✅ `tradingagents/config/redis_manager.py`
   - Removed `load_dotenv()` logic
   - Changed to use `DEFAULT_CONFIG`
   - Removed `_parse_bool()` helper

3. ✅ `tradingagents/config/mongodb_manager.py`
   - Removed `load_dotenv()` logic
   - Changed to use `DEFAULT_CONFIG`
   - Kept optional auth env vars

## Testing

### Verify Configuration Loading
```python
python -c "from tradingagents.default_config import DEFAULT_CONFIG; \
print('Redis:', DEFAULT_CONFIG.get('redis_enabled')); \
print('MongoDB:', DEFAULT_CONFIG.get('mongodb_enabled'))"
```

### Expected Output (with .env configured):
```
Redis: True
MongoDB: True
```

### Test Managers
```python
from tradingagents.config.redis_manager import RedisManager
from tradingagents.config.mongodb_manager import MongoDBManager

redis_mgr = RedisManager()
print(f"Redis available: {redis_mgr.available}")

mongo_mgr = MongoDBManager()
print(f"MongoDB available: {mongo_mgr.available}")
```

## Migration Notes

### For Developers
- **No API changes** - Managers work exactly the same from outside
- **Internal changes only** - Config source changed, behavior unchanged
- **No .env changes needed** - Same environment variables, just loaded differently

### Environment Variables
All existing `.env` variables still work:
```env
# Redis
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379

# MongoDB  
MONGODB_ENABLED=true
MONGODB_HOST=localhost
MONGODB_PORT=27017
```

## Design Principles

### 1. Separation of Concerns
- **Configuration Loading** → `default_config.py`
- **Connection Management** → Manager classes
- **Business Logic** → Application code

### 2. DRY (Don't Repeat Yourself)
- Config loaded once
- No duplicate definitions
- Single modification point

### 3. Explicit Dependencies
```python
from tradingagents.default_config import DEFAULT_CONFIG
# Explicit: This module depends on DEFAULT_CONFIG
```

### 4. Fail-Fast
- Config errors caught at import time
- Missing `.env` → uses defaults
- Invalid values → exception on first access

## Future Improvements

### Possible Enhancements:
1. **Type Safety** - Use Pydantic/dataclass for config validation
2. **Config Sections** - Group related settings into nested dicts
3. **Environment-Specific** - dev.env, prod.env, test.env
4. **Dynamic Reload** - Hot-reload config without restart
5. **Config Validation** - Validate all values at startup

## Date Completed
2026-01-10

## Related Documentation
- [MongoDB Integration](./MONGODB_COMPLETE.md)
- [Phase 1 Caching](./PHASE1_CACHE_INTEGRATION.md)
- [.env Loading Fix](./DOTENV_LOADING_FIX.md)

