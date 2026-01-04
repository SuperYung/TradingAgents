"""
Enhanced file-based cache system
Stores cache in root directory for easy maintenance
MongoDB/WebUI-ready design
"""

import os
import json
import pickle
import hashlib
import logging
from pathlib import Path
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

from tradingagents.config.cache_config import CacheConfig

logger = logging.getLogger(__name__)


class EnhancedFileCache:
    """
    Enhanced file-based cache with organized structure
    
    Features:
    - Root-level cache directory (easy maintenance)
    - Organized by data type
    - JSON metadata for each cache entry
    - Automatic cleanup of expired entries
    - Statistics tracking
    - MongoDB-ready design
    """
    
    def __init__(self, base_dir: str = None):
        """
        Initialize file cache
        
        Args:
            base_dir: Base cache directory (default: cache_data in project root)
        """
        if base_dir is None:
            # Use root-level cache directory
            base_dir = CacheConfig.get_cache_dir('file_cache')
        
        self.base_dir = Path(base_dir)
        self.config = CacheConfig()
        
        # Create cache structure
        self._create_directory_structure()
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'writes': 0,
            'deletes': 0
        }
        
        logger.info(f"📁 File cache initialized: {self.base_dir}")
    
    def _create_directory_structure(self):
        """Create organized cache directory structure"""
        # Main cache directory
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories by data type
        self.subdirs = {
            'stock_quotes': self.base_dir / 'stock_quotes',
            'historical_data': self.base_dir / 'historical_data',
            'fundamentals': self.base_dir / 'fundamentals',
            'news': self.base_dir / 'news',
            'indicators': self.base_dir / 'indicators',
            'metadata': self.base_dir / '_metadata',  # Store cache metadata
        }
        
        for subdir in self.subdirs.values():
            subdir.mkdir(parents=True, exist_ok=True)
        
        # Create README
        readme_path = self.base_dir / 'README.md'
        if not readme_path.exists():
            readme_path.write_text("""# TradingAgents Cache Directory

This directory stores cached data to improve performance and reduce API calls.

## Structure

- `stock_quotes/` - Real-time stock quote data
- `historical_data/` - Historical OHLCV data  
- `fundamentals/` - Fundamental data (balance sheets, income statements, etc.)
- `news/` - News articles and sentiment data
- `indicators/` - Technical indicator calculations
- `_metadata/` - Cache metadata and statistics

## Maintenance

- Cache entries expire automatically based on TTL settings
- Run `python -m tradingagents.utils.cache_monitor --clean` to manually clean expired entries
- Safe to delete entire directory to clear all caches

## Configuration

TTL and size limits are configured in `.env` file:
- `FILE_CACHE_MAX_AGE_DAYS` - Max age before cleanup (default: 7 days)
- `FILE_CACHE_MAX_SIZE_GB` - Max total cache size (default: 2 GB)
""")
    
    def _get_cache_path(self, data_type: str, cache_key: str) -> tuple[Path, Path]:
        """
        Get file paths for cache data and metadata
        
        Returns:
            (data_file_path, metadata_file_path)
        """
        # Map data_type to subdirectory
        subdir_map = {
            'stock_quote': 'stock_quotes',
            'historical_data': 'historical_data',
            'fundamentals': 'fundamentals',
            'balance_sheet': 'fundamentals',
            'income_statement': 'fundamentals',
            'cashflow': 'fundamentals',
            'news': 'news',
            'global_news': 'news',
            'indicators': 'indicators',
        }
        
        subdir_name = subdir_map.get(data_type, 'stock_quotes')
        subdir = self.subdirs[subdir_name]
        
        # Create safe filename from cache key
        safe_key = hashlib.md5(cache_key.encode()).hexdigest()
        
        data_file = subdir / f"{safe_key}.pkl"
        meta_file = self.subdirs['metadata'] / f"{safe_key}.json"
        
        return data_file, meta_file
    
    def get(self, cache_key: str, data_type: str = 'stock_quote') -> Optional[Any]:
        """
        Get data from cache
        
        Args:
            cache_key: Cache key
            data_type: Type of data (for TTL lookup)
        
        Returns:
            Cached data or None
        """
        data_file, meta_file = self._get_cache_path(data_type, cache_key)
        
        # Check if files exist
        if not data_file.exists() or not meta_file.exists():
            self.stats['misses'] += 1
            return None
        
        try:
            # Read metadata
            with open(meta_file, 'r') as f:
                metadata = json.load(f)
            
            # Check if expired
            cached_at = datetime.fromisoformat(metadata['cached_at'])
            ttl = self.config.get_ttl(data_type)
            age = (datetime.now() - cached_at).total_seconds()
            
            if age > ttl:
                # Expired - delete files
                logger.debug(f"Cache expired: {cache_key} (age: {age:.0f}s, TTL: {ttl}s)")
                data_file.unlink(missing_ok=True)
                meta_file.unlink(missing_ok=True)
                self.stats['misses'] += 1
                return None
            
            # Read cached data
            with open(data_file, 'rb') as f:
                data = pickle.load(f)
            
            self.stats['hits'] += 1
            logger.debug(f"✅ Cache HIT: {cache_key} (age: {age:.0f}s)")
            return data
            
        except Exception as e:
            logger.error(f"Error reading cache {cache_key}: {e}")
            # Clean up corrupted files
            data_file.unlink(missing_ok=True)
            meta_file.unlink(missing_ok=True)
            self.stats['misses'] += 1
            return None
    
    def set(self, cache_key: str, data: Any, data_type: str = 'stock_quote', 
            metadata: Dict = None) -> bool:
        """
        Store data in cache
        
        Args:
            cache_key: Cache key
            data: Data to cache
            data_type: Type of data (for TTL lookup)
            metadata: Optional additional metadata
        
        Returns:
            True if cached successfully
        """
        data_file, meta_file = self._get_cache_path(data_type, cache_key)
        
        try:
            # Write data
            with open(data_file, 'wb') as f:
                pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Write metadata
            cache_metadata = {
                'cache_key': cache_key,
                'data_type': data_type,
                'cached_at': datetime.now().isoformat(),
                'ttl_seconds': self.config.get_ttl(data_type),
                'data_file': str(data_file),
                'size_bytes': data_file.stat().st_size,
            }
            
            if metadata:
                cache_metadata.update(metadata)
            
            with open(meta_file, 'w') as f:
                json.dump(cache_metadata, f, indent=2)
            
            self.stats['writes'] += 1
            logger.debug(f"💾 Cache SET: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error writing cache {cache_key}: {e}")
            # Clean up partial writes
            data_file.unlink(missing_ok=True)
            meta_file.unlink(missing_ok=True)
            return False
    
    def delete(self, cache_key: str, data_type: str = 'stock_quote') -> bool:
        """Delete cache entry"""
        data_file, meta_file = self._get_cache_path(data_type, cache_key)
        
        try:
            data_file.unlink(missing_ok=True)
            meta_file.unlink(missing_ok=True)
            self.stats['deletes'] += 1
            return True
        except Exception as e:
            logger.error(f"Error deleting cache {cache_key}: {e}")
            return False
    
    def clear_expired(self) -> int:
        """
        Clear all expired cache entries
        
        Returns:
            Number of entries deleted
        """
        deleted = 0
        
        # Check all metadata files
        for meta_file in self.subdirs['metadata'].glob('*.json'):
            try:
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                
                cached_at = datetime.fromisoformat(metadata['cached_at'])
                ttl = metadata.get('ttl_seconds', 3600)
                age = (datetime.now() - cached_at).total_seconds()
                
                if age > ttl:
                    # Expired - delete
                    cache_key = metadata['cache_key']
                    data_type = metadata.get('data_type', 'stock_quote')
                    if self.delete(cache_key, data_type):
                        deleted += 1
                        
            except Exception as e:
                logger.error(f"Error checking expiry for {meta_file}: {e}")
        
        if deleted > 0:
            logger.info(f"🧹 Cleaned {deleted} expired cache entries")
        
        return deleted
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_files = sum(1 for _ in self.base_dir.rglob('*.pkl'))
        total_size = sum(f.stat().st_size for f in self.base_dir.rglob('*') if f.is_file())
        
        return {
            'enabled': True,
            'base_dir': str(self.base_dir),
            'total_entries': total_files,
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'writes': self.stats['writes'],
            'deletes': self.stats['deletes'],
            'hit_rate': round(self.stats['hits'] / max(self.stats['hits'] + self.stats['misses'], 1) * 100, 1)
        }


# Global instance
_file_cache: Optional[EnhancedFileCache] = None


def get_file_cache() -> EnhancedFileCache:
    """Get global file cache instance"""
    global _file_cache
    if _file_cache is None:
        _file_cache = EnhancedFileCache()
    return _file_cache

