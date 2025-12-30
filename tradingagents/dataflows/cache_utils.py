"""
Cache utilities for TradingAgents.
Implements file-based caching with TTL support to avoid redundant API calls.
"""

import json
import os
import time
import hashlib
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional
from .config import get_config


def get_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from function arguments."""
    # Create a stable string representation of args and kwargs
    key_data = {
        "args": args,
        "kwargs": kwargs
    }
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()


def get_cache_path(func_name: str, cache_key: str) -> Path:
    """Get the file path for a cache entry."""
    config = get_config()
    cache_dir = Path(config.get("cache_dir", "./cache"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectory for function
    func_cache_dir = cache_dir / func_name
    func_cache_dir.mkdir(exist_ok=True)
    
    return func_cache_dir / f"{cache_key}.json"


def is_cache_valid(cache_file: Path, ttl_seconds: int) -> bool:
    """Check if a cache file exists and is still valid."""
    if not cache_file.exists():
        return False
    
    # Check if cache has expired
    file_age = time.time() - cache_file.stat().st_mtime
    return file_age < ttl_seconds


def read_cache(cache_file: Path) -> Optional[Any]:
    """Read data from cache file."""
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            return cache_data.get('result')
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading cache file {cache_file}: {e}")
        return None


def write_cache(cache_file: Path, result: Any) -> None:
    """Write data to cache file."""
    try:
        cache_data = {
            'timestamp': time.time(),
            'result': result
        }
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, default=str)
    except (IOError, TypeError) as e:
        print(f"Error writing cache file {cache_file}: {e}")


def cached(ttl_seconds: Optional[int] = None, cache_key_func: Optional[Callable] = None):
    """
    Decorator to cache function results with TTL.
    
    Args:
        ttl_seconds: Time to live in seconds. If None, uses config default.
        cache_key_func: Optional function to generate custom cache key from args.
    
    Example:
        @cached(ttl_seconds=3600)
        def get_stock_data(ticker, start_date, end_date):
            # Expensive API call here
            return data
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            config = get_config()
            ttl = ttl_seconds if ttl_seconds is not None else config.get("cache_ttl_seconds", 3600)
            
            # Generate cache key
            if cache_key_func:
                cache_key = cache_key_func(*args, **kwargs)
            else:
                cache_key = get_cache_key(*args, **kwargs)
            
            cache_file = get_cache_path(func.__name__, cache_key)
            
            # Check if valid cache exists
            if is_cache_valid(cache_file, ttl):
                result = read_cache(cache_file)
                if result is not None:
                    if config.get("debug", False):
                        print(f"Cache hit for {func.__name__} with key {cache_key[:8]}...")
                    return result
            
            # Cache miss or expired - call function
            if config.get("debug", False):
                print(f"Cache miss for {func.__name__} with key {cache_key[:8]}...")
            
            result = func(*args, **kwargs)
            
            # Write to cache
            write_cache(cache_file, result)
            
            return result
        
        return wrapper
    return decorator


def clear_cache(func_name: Optional[str] = None) -> None:
    """
    Clear cache entries.
    
    Args:
        func_name: If provided, clear cache for specific function only.
                  If None, clear all cache.
    """
    config = get_config()
    cache_dir = Path(config.get("cache_dir", "./cache"))
    
    if not cache_dir.exists():
        return
    
    if func_name:
        # Clear specific function cache
        func_cache_dir = cache_dir / func_name
        if func_cache_dir.exists():
            for cache_file in func_cache_dir.glob("*.json"):
                cache_file.unlink()
            print(f"Cleared cache for {func_name}")
    else:
        # Clear all cache
        for func_cache_dir in cache_dir.iterdir():
            if func_cache_dir.is_dir():
                for cache_file in func_cache_dir.glob("*.json"):
                    cache_file.unlink()
        print("Cleared all cache")


# Convenience function for ticker-based caching (common use case)
def ticker_cache_key(ticker: str, *args, **kwargs) -> str:
    """Generate cache key primarily based on ticker symbol."""
    # Normalize ticker to uppercase
    ticker_upper = ticker.upper()
    
    # Include other args in the key
    key_data = {
        "ticker": ticker_upper,
        "args": args,
        "kwargs": kwargs
    }
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()


if __name__ == "__main__":
    # Example usage
    @cached(ttl_seconds=10)
    def expensive_function(x, y):
        print(f"Computing {x} + {y}...")
        time.sleep(2)
        return x + y
    
    # First call - cache miss
    print("First call:")
    result = expensive_function(5, 3)
    print(f"Result: {result}")
    
    # Second call - cache hit (should be instant)
    print("\nSecond call:")
    result = expensive_function(5, 3)
    print(f"Result: {result}")
    
    # Different arguments - cache miss
    print("\nThird call with different args:")
    result = expensive_function(10, 20)
    print(f"Result: {result}")
    
    # Clear cache
    print("\nClearing cache...")
    clear_cache("expensive_function")

