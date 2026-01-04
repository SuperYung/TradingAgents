"""
Integrated cache manager combining Redis and File cache
Multi-tier caching: Redis (L1) → File (L2) → API
MongoDB-ready design for future expansion
"""

import json
import hashlib
import logging
from typing import Any, Optional, Dict
from datetime import datetime

from tradingagents.config.redis_manager import get_redis_manager
from tradingagents.config.cache_config import CacheConfig
from tradingagents.dataflows.cache.enhanced_file_cache import get_file_cache

logger = logging.getLogger(__name__)


class IntegratedCache:
    """
    Multi-tier cache manager with automatic fallback
    
    Architecture:
    1. Redis (L1) - Fastest, in-memory cache
    2. File (L2) - Persistent fallback
    3. API - Data source (fallback if all caches miss)
    
    Features:
    - Automatic fallback if Redis unavailable
    - Graceful degradation
    - Statistics tracking
    - MongoDB-ready (will add as L1.5 in future)
    """
    
    def __init__(self):
        # Initialize cache backends
        self.redis_manager = get_redis_manager()
        self.redis = self.redis_manager.get_client()
        self.file_cache = get_file_cache()
        self.config = CacheConfig()
        
        # Cache statistics
        self.stats = {
            'redis_hits': 0,
            'redis_misses': 0,
            'file_hits': 0,
            'file_misses': 0,
            'total_requests': 0,
        }
        
        # Determine cache mode
        self.mode = self._determine_mode()
        logger.info(f"🚀 Cache Mode: {self.mode}")
    
    def _determine_mode(self) -> str:
        """Determine current cache mode"""
        if self.redis:
            return "High-Performance (Redis + File)"
        else:
            return "Standard (File Only)"
    
    def _generate_cache_key(self, data_type: str, **params) -> str:
        """
        Generate consistent cache key from parameters
        
        Args:
            data_type: Type of data
            **params: Parameters identifying the data
        
        Returns:
            Cache key string
        """
        # Sort parameters for consistent keys
        key_parts = [data_type]
        for k, v in sorted(params.items()):
            key_parts.append(f"{k}={v}")
        
        key_string = ":".join(key_parts)
        return key_string
    
    def _generate_redis_key(self, cache_key: str) -> str:
        """Generate Redis key with prefix"""
        # Use short hash for Redis efficiency
        key_hash = hashlib.md5(cache_key.encode()).hexdigest()[:16]
        return f"ta:{key_hash}"
    
    def get(self, data_type: str, **params) -> Optional[Any]:
        """
        Get from cache with automatic fallback
        
        Flow:
        1. Try Redis (if available)
        2. Try File cache
        3. Return None (caller should fetch from API)
        
        Args:
            data_type: Type of data (e.g., 'stock_quote', 'fundamentals')
            **params: Parameters to identify the data
        
        Returns:
            Cached data or None
        """
        self.stats['total_requests'] += 1
        cache_key = self._generate_cache_key(data_type, **params)
        
        # L1: Try Redis first
        if self.redis:
            try:
                redis_key = self._generate_redis_key(cache_key)
                cached_json = self.redis.get(redis_key)
                
                if cached_json:
                    self.stats['redis_hits'] += 1
                    logger.debug(f"✅ Redis HIT: {data_type} {params}")
                    return json.loads(cached_json)
                else:
                    self.stats['redis_misses'] += 1
                    
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
                self.stats['redis_misses'] += 1
        
        # L2: Try File cache
        try:
            data = self.file_cache.get(cache_key, data_type)
            if data is not None:
                self.stats['file_hits'] += 1
                logger.debug(f"✅ File HIT: {data_type} {params}")
                
                # Promote to Redis if available
                if self.redis:
                    self._set_redis(cache_key, data, data_type)
                
                return data
            else:
                self.stats['file_misses'] += 1
                
        except Exception as e:
            logger.error(f"File cache get error: {e}")
            self.stats['file_misses'] += 1
        
        # Cache miss - caller should fetch from API
        logger.debug(f"❌ Cache MISS: {data_type} {params}")
        return None
    
    def set(self, data_type: str, data: Any, **params) -> bool:
        """
        Store in all cache tiers
        
        Args:
            data_type: Type of data
            data: Data to cache
            **params: Parameters identifying the data
        
        Returns:
            True if successfully cached in at least one tier
        """
        cache_key = self._generate_cache_key(data_type, **params)
        success = False
        
        # Store in Redis
        if self.redis:
            if self._set_redis(cache_key, data, data_type):
                success = True
        
        # Store in File cache
        try:
            metadata = {
                'data_type': data_type,
                'params': params,
                'cached_by': 'integrated_cache'
            }
            if self.file_cache.set(cache_key, data, data_type, metadata):
                success = True
        except Exception as e:
            logger.error(f"File cache set error: {e}")
        
        if success:
            logger.debug(f"💾 Cache SET: {data_type} {params}")
        
        return success
    
    def _set_redis(self, cache_key: str, data: Any, data_type: str) -> bool:
        """Store in Redis with TTL"""
        try:
            redis_key = self._generate_redis_key(cache_key)
            ttl = self.config.get_ttl(data_type)
            
            self.redis.setex(
                redis_key,
                ttl,
                json.dumps(data, default=str)
            )
            return True
        except Exception as e:
            logger.warning(f"Redis set error: {e}")
            return False
    
    def delete(self, data_type: str, **params) -> bool:
        """Delete from all cache tiers"""
        cache_key = self._generate_cache_key(data_type, **params)
        success = False
        
        # Delete from Redis
        if self.redis:
            try:
                redis_key = self._generate_redis_key(cache_key)
                self.redis.delete(redis_key)
                success = True
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
        
        # Delete from File cache
        if self.file_cache.delete(cache_key, data_type):
            success = True
        
        return success
    
    def clear_pattern(self, pattern: str = "*") -> Dict[str, int]:
        """
        Clear cache entries matching pattern
        
        Args:
            pattern: Pattern to match (Redis pattern syntax)
        
        Returns:
            Dict with counts: {'redis': N, 'file': M}
        """
        result = {'redis': 0, 'file': 0}
        
        # Clear from Redis
        if self.redis:
            try:
                if pattern == "*":
                    redis_pattern = "ta:*"
                else:
                    redis_pattern = f"ta:{pattern}*"
                
                keys = self.redis.keys(redis_pattern)
                if keys:
                    result['redis'] = self.redis.delete(*keys)
            except Exception as e:
                logger.error(f"Redis clear error: {e}")
        
        # Clear from File cache (clear expired only for now)
        try:
            result['file'] = self.file_cache.clear_expired()
        except Exception as e:
            logger.error(f"File cache clear error: {e}")
        
        total = result['redis'] + result['file']
        if total > 0:
            logger.info(f"🧹 Cleared {total} cache entries (Redis: {result['redis']}, File: {result['file']})")
        
        return result
    
    def get_stats(self) -> Dict:
        """Get comprehensive cache statistics"""
        redis_stats = self.redis_manager.get_stats() if self.redis else {'available': False}
        file_stats = self.file_cache.get_stats()
        
        total_hits = self.stats['redis_hits'] + self.stats['file_hits']
        total_misses = self.stats['redis_misses'] + self.stats['file_misses']
        total_requests = self.stats['total_requests']
        
        overall_hit_rate = 0
        if total_requests > 0:
            overall_hit_rate = round(total_hits / total_requests * 100, 1)
        
        return {
            'mode': self.mode,
            'overall': {
                'total_requests': total_requests,
                'total_hits': total_hits,
                'total_misses': total_misses,
                'hit_rate': overall_hit_rate,
            },
            'redis': {
                'available': redis_stats.get('available', False),
                'hits': self.stats['redis_hits'],
                'misses': self.stats['redis_misses'],
                **redis_stats
            },
            'file': {
                'hits': self.stats['file_hits'],
                'misses': self.stats['file_misses'],
                **file_stats
            }
        }
    
    def print_stats(self):
        """Print formatted cache statistics"""
        stats = self.get_stats()
        
        print("\n" + "=" * 70)
        print("CACHE STATISTICS")
        print("=" * 70)
        
        print(f"\n🎯 Mode: {stats['mode']}")
        
        overall = stats['overall']
        print(f"\n📊 Overall:")
        print(f"  Total Requests: {overall['total_requests']}")
        print(f"  Total Hits: {overall['total_hits']}")
        print(f"  Total Misses: {overall['total_misses']}")
        print(f"  Hit Rate: {overall['hit_rate']}%")
        
        redis = stats['redis']
        print(f"\n🔴 Redis:")
        print(f"  Available: {'✅ Yes' if redis['available'] else '❌ No'}")
        if redis['available']:
            print(f"  Hits: {redis['hits']}")
            print(f"  Misses: {redis['misses']}")
            print(f"  Keys: {redis.get('keys', 0)}")
            print(f"  Memory: {redis.get('memory', 'N/A')}")
        
        file = stats['file']
        print(f"\n📁 File Cache:")
        print(f"  Hits: {file['hits']}")
        print(f"  Misses: {file['misses']}")
        print(f"  Total Entries: {file['total_entries']}")
        print(f"  Total Size: {file['total_size_mb']} MB")
        print(f"  Hit Rate: {file['hit_rate']}%")
        
        print("=" * 70 + "\n")


# Global instance
_integrated_cache: Optional[IntegratedCache] = None


def get_cache() -> IntegratedCache:
    """Get global integrated cache instance"""
    global _integrated_cache
    if _integrated_cache is None:
        _integrated_cache = IntegratedCache()
    return _integrated_cache

