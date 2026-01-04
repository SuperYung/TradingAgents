"""
Cache management system for TradingAgents

Provides multi-tier caching:
- Redis (L1): Fast in-memory cache
- File (L2): Persistent disk cache
- Automatic fallback and graceful degradation

Usage:
    from tradingagents.dataflows.cache import get_cache
    
    cache = get_cache()
    
    # Get from cache
    data = cache.get('stock_quote', symbol='AAPL')
    
    # Set to cache
    cache.set('stock_quote', data, symbol='AAPL')
"""

from .integrated_cache import IntegratedCache, get_cache
from .enhanced_file_cache import EnhancedFileCache, get_file_cache

__all__ = [
    'IntegratedCache',
    'get_cache',
    'EnhancedFileCache',
    'get_file_cache',
]

