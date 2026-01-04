"""
Redis connection manager with graceful fallback
Designed to be MongoDB/WebUI-ready for future expansion
"""

import redis
import logging
import os
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class RedisManager:
    """
    Manages Redis connection with automatic fallback
    
    Features:
    - Auto-detection of Redis availability
    - Graceful fallback if Redis unavailable
    - Connection pooling
    - Health monitoring
    - MongoDB-ready design (will add MongoDB client here in future)
    """
    
    def __init__(self):
        self.enabled = self._parse_bool(os.getenv("REDIS_ENABLED", "false"))
        self.redis_client: Optional[redis.Redis] = None
        self.available = False
        
        # Future: MongoDB client will be initialized here
        self.mongodb_client = None
        self.mongodb_available = False
        
        if self.enabled:
            self._initialize_redis()
        else:
            logger.info("📦 Redis disabled, using file cache only")
    
    def _parse_bool(self, value: str) -> bool:
        """Parse boolean from environment variable"""
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def _initialize_redis(self):
        """Initialize Redis connection with connection pooling"""
        try:
            # Create connection pool for better performance
            pool = redis.ConnectionPool(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                password=os.getenv("REDIS_PASSWORD") or None,
                db=int(os.getenv("REDIS_DB", "0")),
                max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "10")),
                decode_responses=True,  # Auto-decode bytes to strings
                socket_timeout=2,
                socket_connect_timeout=2,
                retry_on_timeout=True,
                health_check_interval=30  # Check connection health every 30s
            )
            
            self.redis_client = redis.Redis(connection_pool=pool)
            
            # Test connection
            self.redis_client.ping()
            self.available = True
            
            # Get Redis info
            info = self.redis_client.info('server')
            version = info.get('redis_version', 'unknown')
            
            logger.info(f"✅ Redis connected successfully (v{version})")
            logger.info(f"   Host: {os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}")
            
        except redis.ConnectionError as e:
            logger.warning(f"⚠️  Redis connection failed: {e}")
            logger.info("   Falling back to file cache only")
            self.available = False
            self.redis_client = None
            
        except Exception as e:
            logger.warning(f"⚠️  Redis initialization error: {e}")
            logger.info("   Falling back to file cache only")
            self.available = False
            self.redis_client = None
    
    def get_client(self) -> Optional[redis.Redis]:
        """Get Redis client if available"""
        return self.redis_client if self.available else None
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        if not self.available:
            return False
        
        # Quick health check
        try:
            self.redis_client.ping()
            return True
        except:
            logger.warning("⚠️  Redis connection lost")
            self.available = False
            return False
    
    def get_stats(self) -> dict:
        """Get Redis statistics"""
        if not self.available or not self.redis_client:
            return {
                'available': False,
                'keys': 0,
                'memory': 'N/A'
            }
        
        try:
            info = self.redis_client.info()
            return {
                'available': True,
                'keys': self.redis_client.dbsize(),
                'memory': info.get('used_memory_human', 'N/A'),
                'memory_peak': info.get('used_memory_peak_human', 'N/A'),
                'connected_clients': info.get('connected_clients', 0),
                'uptime_days': info.get('uptime_in_days', 0),
                'version': info.get('redis_version', 'unknown')
            }
        except Exception as e:
            logger.error(f"Error getting Redis stats: {e}")
            return {
                'available': False,
                'error': str(e)
            }
    
    def clear_cache(self, pattern: str = "ta:*") -> int:
        """
        Clear cache entries matching pattern
        
        Args:
            pattern: Redis key pattern (default: ta:* for all TradingAgents keys)
        
        Returns:
            Number of keys deleted
        """
        if not self.available or not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"🧹 Cleared {deleted} Redis cache entries")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Error clearing Redis cache: {e}")
            return 0
    
    def close(self):
        """Close Redis connection"""
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("✅ Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")


# Global instance (singleton pattern)
_redis_manager: Optional[RedisManager] = None


def get_redis_manager() -> RedisManager:
    """Get global Redis manager instance"""
    global _redis_manager
    if _redis_manager is None:
        _redis_manager = RedisManager()
    return _redis_manager


def get_redis_client() -> Optional[redis.Redis]:
    """Quick access to Redis client"""
    return get_redis_manager().get_client()

