"""
Configuration management for TradingAgents
Handles Redis, cache settings, and database connections
"""

from .redis_manager import RedisManager, get_redis_manager, get_redis_client
from .cache_config import CacheConfig

__all__ = [
    'RedisManager',
    'get_redis_manager',
    'get_redis_client',
    'CacheConfig',
]

