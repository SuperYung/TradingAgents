# .env File Not Loading - Fix

## Issue

Redis is running and enabled in `.env`, but Python shows "Redis disabled, using file cache only".

## Root Cause

Python doesn't automatically load `.env` files. You need `python-dotenv` package.

## Fix

### Step 1: Install python-dotenv

```bash
pip install python-dotenv
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### Step 2: Restart your application

```bash
python -m tradingagents.utils.cache_monitor --health
```

**Expected output**:
```
🔴 Redis: ✅ Healthy
   Keys: 0
   Memory: 1.2MB
   
🎯 Overall:
   Mode: High-Performance (Redis + File)
```

## Alternative: Set Environment Variables Directly

If you don't want to use `.env` file:

### Windows PowerShell:
```powershell
$env:REDIS_ENABLED="true"
$env:REDIS_HOST="localhost"  
$env:REDIS_PORT="6379"

python -m tradingagents.utils.cache_monitor --health
```

### Windows CMD:
```cmd
set REDIS_ENABLED=true
set REDIS_HOST=localhost
set REDIS_PORT=6379

python -m tradingagents.utils.cache_monitor --health
```

### Linux/Mac:
```bash
export REDIS_ENABLED=true
export REDIS_HOST=localhost
export REDIS_PORT=6379

python -m tradingagents.utils.cache_monitor --health
```

## Verify .env Format

Make sure your `.env` file has correct format:

```bash
# ✅ Correct:
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379

# ❌ Wrong (don't use quotes or spaces):
REDIS_ENABLED = "true"
REDIS_ENABLED= true
```

## Update (January 2025)

The code has been updated to automatically load `.env` files when `python-dotenv` is installed. Just run:

```bash
pip install python-dotenv
```

Then Redis will work automatically!

