"""
Cache configuration and TTL settings
Centralized configuration for all cache types
"""

import os
from typing import Dict


class CacheConfig:
    """
    Centralized cache TTL configuration for different data types
    
    Design Philosophy:
    - Real-time data: Short TTL (1-5 minutes)
    - Historical data: Medium TTL (1 hour)
    - Fundamentals: Long TTL (24 hours)
    - Configurable via environment variables
    """
    
    # Default TTL values (in seconds)
    DEFAULTS = {
        # Core stock data
        'stock_quote': 60,              # 1 minute - real-time quotes
        'historical_data': 3600,        # 1 hour - historical OHLCV
        'stock_info': 86400,            # 24 hours - company information
        
        # Technical indicators
        'indicators': 3600,             # 1 hour - technical indicators
        
        # Fundamental data
        'fundamentals': 86400,          # 24 hours - fundamental metrics
        'balance_sheet': 86400,         # 24 hours - balance sheet
        'income_statement': 86400,      # 24 hours - income statement
        'cashflow': 86400,              # 24 hours - cash flow statement
        
        # News data
        'news': 1800,                   # 30 minutes - news articles
        'global_news': 3600,            # 1 hour - global market news
        'insider_sentiment': 3600,      # 1 hour - insider sentiment
        'insider_transactions': 3600,   # 1 hour - insider transactions
        
        # Analysis results (future use with MongoDB)
        'analysis_result': 86400,       # 24 hours - completed analysis
        'analysis_progress': 300,       # 5 minutes - progress tracking
    }
    
    # Cache directory configuration (root-level for easy maintenance)
    CACHE_DIRS = {
        'redis_cache': None,            # Redis is in-memory
        'file_cache': 'cache_data',     # Root-level cache directory
        'analysis_results': 'data/analysis_results',  # Analysis outputs
        'mongodb_backup': 'data/mongodb_backup',      # MongoDB backups (future)
    }
    
    @classmethod
    def get_ttl(cls, data_type: str) -> int:
        """
        Get TTL for a specific data type
        
        Args:
            data_type: Type of data (e.g., 'stock_quote', 'fundamentals')
        
        Returns:
            TTL in seconds
        """
        # Check environment variable first
        env_key = f"CACHE_TTL_{data_type.upper()}"
        env_value = os.getenv(env_key)
        
        if env_value:
            try:
                return int(env_value)
            except ValueError:
                pass
        
        # Fall back to default
        return cls.DEFAULTS.get(data_type, 3600)  # Default to 1 hour
    
    @classmethod
    def get_all_ttls(cls) -> Dict[str, int]:
        """Get all configured TTLs"""
        return {
            data_type: cls.get_ttl(data_type)
            for data_type in cls.DEFAULTS.keys()
        }
    
    @classmethod
    def get_cache_dir(cls, cache_type: str) -> str:
        """Get cache directory path"""
        return cls.CACHE_DIRS.get(cache_type, 'cache_data')
    
    @classmethod
    def get_file_cache_config(cls) -> dict:
        """Get file cache configuration"""
        return {
            'enabled': os.getenv('FILE_CACHE_ENABLED', 'true').lower() == 'true',
            'base_dir': cls.get_cache_dir('file_cache'),
            'max_age_days': int(os.getenv('FILE_CACHE_MAX_AGE_DAYS', '7')),
            'max_size_gb': float(os.getenv('FILE_CACHE_MAX_SIZE_GB', '2')),
            'cleanup_on_startup': os.getenv('FILE_CACHE_CLEANUP_ON_STARTUP', 'false').lower() == 'true',
        }
    
    @classmethod
    def get_redis_config(cls) -> dict:
        """Get Redis configuration"""
        return {
            'enabled': os.getenv('REDIS_ENABLED', 'false').lower() == 'true',
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', '6379')),
            'password': os.getenv('REDIS_PASSWORD'),
            'db': int(os.getenv('REDIS_DB', '0')),
            'max_connections': int(os.getenv('REDIS_MAX_CONNECTIONS', '10')),
            'key_prefix': 'ta:',  # TradingAgents prefix for all keys
        }
    
    @classmethod
    def get_mongodb_config(cls) -> dict:
        """
        Get MongoDB configuration (future use)
        Ready for Phase 2 MongoDB integration
        """
        return {
            'enabled': os.getenv('MONGODB_ENABLED', 'false').lower() == 'true',
            'host': os.getenv('MONGODB_HOST', 'localhost'),
            'port': int(os.getenv('MONGODB_PORT', '27017')),
            'username': os.getenv('MONGODB_USERNAME'),
            'password': os.getenv('MONGODB_PASSWORD'),
            'database': os.getenv('MONGODB_DATABASE', 'tradingagents'),
            'auth_source': os.getenv('MONGODB_AUTH_SOURCE', 'admin'),
        }
    
    @classmethod
    def print_config(cls):
        """Print current cache configuration (useful for debugging)"""
        print("=" * 60)
        print("CACHE CONFIGURATION")
        print("=" * 60)
        
        print("\n📊 TTL Settings:")
        for data_type, ttl in cls.get_all_ttls().items():
            minutes = ttl / 60
            hours = ttl / 3600
            if hours >= 1:
                print(f"  {data_type:25s}: {ttl:6d}s ({hours:.1f}h)")
            else:
                print(f"  {data_type:25s}: {ttl:6d}s ({minutes:.1f}m)")
        
        redis_conf = cls.get_redis_config()
        print(f"\n🔴 Redis:")
        print(f"  Enabled: {redis_conf['enabled']}")
        if redis_conf['enabled']:
            print(f"  Host: {redis_conf['host']}:{redis_conf['port']}")
            print(f"  DB: {redis_conf['db']}")
        
        file_conf = cls.get_file_cache_config()
        print(f"\n📁 File Cache:")
        print(f"  Enabled: {file_conf['enabled']}")
        print(f"  Directory: {file_conf['base_dir']}")
        print(f"  Max Age: {file_conf['max_age_days']} days")
        print(f"  Max Size: {file_conf['max_size_gb']} GB")
        
        mongo_conf = cls.get_mongodb_config()
        print(f"\n🍃 MongoDB (Future):")
        print(f"  Enabled: {mongo_conf['enabled']}")
        if mongo_conf['enabled']:
            print(f"  Host: {mongo_conf['host']}:{mongo_conf['port']}")
            print(f"  Database: {mongo_conf['database']}")
        
        print("=" * 60)

