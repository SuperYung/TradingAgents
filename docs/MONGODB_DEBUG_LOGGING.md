# MongoDB Save Debugging Guide

## Added Debug Logging (2026-01-10)

### Purpose
Added comprehensive logging to trace the entire MongoDB save flow and identify why analysis counts remain at 0.

## What Was Added

### 1. trading_graph.py - _save_to_mongodb()
**Added logs for:**
- ✅ Config check: `mongodb_enabled` flag
- ✅ Config check: `mongodb_save_analyses` flag
- ✅ Repository initialization
- ✅ Collection availability check
- ✅ Analysis ID generation
- ✅ Document building
- ✅ save_analysis() call and result
- ✅ Exception handling with full traceback

**Log markers:** `🔍 [MongoDB Save]`, `✅ [MongoDB Save]`, `❌ [MongoDB Save]`, `⚠️ [MongoDB Save]`

### 2. analysis_repository.py - save_analysis()
**Added logs for:**
- ✅ Method entry
- ✅ Collection availability
- ✅ Required field validation
- ✅ MongoDB replace_one() call
- ✅ Result inspection (upserted_id, modified_count)
- ✅ Exception handling with full traceback

**Log markers:** `🔍 [AnalysisRepo]`, `✅ [AnalysisRepo]`, `❌ [AnalysisRepo]`, `⚠️ [AnalysisRepo]`

### 3. mongodb_manager.py - __init__()
**Added logs for:**
- ✅ Initialization start
- ✅ Config flag check
- ✅ Enable/disable warnings

**Log markers:** `🔍 [MongoDBManager]`, `✅ [MongoDBManager]`, `⚠️ [MongoDBManager]`

## How to Use

### 1. Set Log Level to INFO
Make sure your `.env` has:
```env
TRADINGAGENTS_LOG_LEVEL=INFO
```

### 2. Run an Analysis
```bash
python -m cli.main
```

### 3. Watch the Logs
Logs are written to: `logs/tradingagents.log`

**Tail the log in real-time:**
```bash
# Windows PowerShell
Get-Content -Path logs\tradingagents.log -Tail 50 -Wait

# Git Bash / WSL
tail -f logs/tradingagents.log

# Or just read the file after completion
cat logs/tradingagents.log | grep "MongoDB"
```

### 4. Check for Specific Issues

#### Issue: MongoDB Disabled
**Look for:**
```
⚠️ [MongoDBManager] MongoDB disabled via MONGODB_ENABLED=false
⚠️ [MongoDBManager] Set MONGODB_ENABLED=true in .env to enable
```
**Fix:** Add `MONGODB_ENABLED=true` to your `.env`

#### Issue: Save Analyses Flag Disabled
**Look for:**
```
⚠️ [MongoDB Save] SKIPPED: mongodb_save_analyses=False
```
**Fix:** Add `MONGODB_SAVE_ANALYSES=true` to your `.env`

#### Issue: Config Not Loaded
**Look for:**
```
🔍 [MongoDB Save] mongodb_enabled=False
```
**Fix:** Restart Python session to reload config, verify `.env` exists in project root

#### Issue: Collection Not Available
**Look for:**
```
❌ [MongoDB Save] FAILED: Repository collection is None
```
**Fix:** Check MongoDB connection, Docker container running

#### Issue: Save Failed
**Look for:**
```
❌ [AnalysisRepo] EXCEPTION saving analysis: ...
```
**Action:** Review the exception traceback for specific error

## Expected Log Flow (Success)

When everything works, you should see this sequence:

```
🔍 [MongoDBManager] Initializing...
🔍 [MongoDBManager] mongodb_enabled from config: True
✅ [MongoDBManager] MongoDB enabled, proceeding with connection...
✅ MongoDB connected successfully
   📊 Database: tradingagents
   🔗 Host: localhost:27017

... (analysis runs) ...

🔍 [MongoDB Save] Attempting to save analysis to MongoDB...
🔍 [MongoDB Save] mongodb_enabled=True
🔍 [MongoDB Save] mongodb_save_analyses=True
✅ [MongoDB Save] Config checks passed, initializing repository...
🔍 [MongoDB Save] Repository initialized, collection=Collection(...)
✅ [MongoDB Save] Repository ready, building analysis document...
🔍 [MongoDB Save] Analysis ID: AAPL_2026-01-10_1736534567
🔍 [MongoDB Save] Analysis document built, calling repo.save_analysis()...

🔍 [AnalysisRepo] save_analysis() called
🔍 [AnalysisRepo] collection=Collection(...)
✅ [AnalysisRepo] Collection available, proceeding...
🔍 [AnalysisRepo] Saving analysis_id: AAPL_2026-01-10_1736534567
🔍 [AnalysisRepo] Calling collection.replace_one()...
🔍 [AnalysisRepo] replace_one result: upserted_id=ObjectId('...'), modified_count=0
✅ [AnalysisRepo] SUCCESS! Analysis saved: AAPL_2026-01-10_1736534567

🔍 [MongoDB Save] repo.save_analysis() returned: True
✅ [MongoDB Save] SUCCESS! Analysis saved: AAPL_2026-01-10_1736534567
```

## Troubleshooting Steps

### Step 1: Verify .env Loaded
Look for early startup logs showing config values.

### Step 2: Verify MongoDB Connected
Look for:
```
✅ MongoDB connected successfully
```

### Step 3: Verify Save Attempt
Look for:
```
🔍 [MongoDB Save] Attempting to save analysis to MongoDB...
```

If you DON'T see this, the `_save_to_mongodb()` method is not being called!

### Step 4: Verify Config Flags
Check the logged values:
```
🔍 [MongoDB Save] mongodb_enabled=True
🔍 [MongoDB Save] mongodb_save_analyses=True
```

If False, config not loaded properly.

### Step 5: Verify Repository
Check collection is not None:
```
🔍 [MongoDB Save] Repository initialized, collection=Collection(Database(MongoClient(...), 'tradingagents'), 'analysis_reports')
```

### Step 6: Verify Save Call
Should see:
```
🔍 [AnalysisRepo] save_analysis() called
```

### Step 7: Verify MongoDB Write
Should see:
```
✅ [AnalysisRepo] SUCCESS! Analysis saved: ...
```

## After Debugging

Once the issue is found and fixed, you can reduce logging verbosity by:
1. Removing the debug logs (or commenting them out)
2. Changing log level back to WARNING or ERROR
3. Keeping only the success/failure logs

## Quick Grep Commands

```bash
# Show all MongoDB-related logs
grep "MongoDB" logs/tradingagents.log

# Show only save attempts
grep "\[MongoDB Save\]" logs/tradingagents.log

# Show only errors
grep "❌" logs/tradingagents.log

# Show only success
grep "✅" logs/tradingagents.log

# Show config values
grep "mongodb_enabled" logs/tradingagents.log
```

## Files Modified
1. `tradingagents/graph/trading_graph.py` - Added detailed save logging
2. `tradingagents/dataflows/mongodb/analysis_repository.py` - Added save method logging
3. `tradingagents/config/mongodb_manager.py` - Added init logging

## Date Added
2026-01-10

