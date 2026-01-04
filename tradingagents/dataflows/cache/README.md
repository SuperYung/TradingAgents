# Cache Directory

This directory is reserved for future file-based caching implementation.

## Current Status

Currently **not actively used** by TradingAgents.

## Caching Architecture

### Active Caching Systems:

1. **In-Memory Cache** (Provider classes)
   - Location: `dataflows/providers/us/*.py`
   - TTL: 3600 seconds (1 hour)
   - Stores: API responses in memory

2. **CSV File Cache** (Historical data)
   - Location: `dataflows/data_cache/`
   - Files: `{symbol}-YFin-data-{start}-{end}.csv`
   - Stores: Historical OHLCV data for technical analysis

3. **ChromaDB** (Vector embeddings for memory)
   - Location: `chroma_db/` (project root)
   - Stores: Agent memory embeddings and metadata

## Future Use

This directory may be used for:
- Tool call result caching
- API response persistence across sessions
- Multi-tier caching strategy

## Note

If you see JSON files appearing here, they may be from:
- Development/debugging artifacts
- Third-party library automatic caching
- Experimental features

These can typically be safely deleted.

