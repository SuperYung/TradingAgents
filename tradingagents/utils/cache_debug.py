"""
Cache Key Diagnostic Tool
Helps debug cache hit/miss issues by inspecting Redis keys
"""

import sys
import os
from pathlib import Path
import json

# Add project root to path (go up 3 levels from this file to reach project root)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.config import get_redis_manager
from tradingagents.dataflows.cache import get_cache


def inspect_redis_keys():
    """Inspect all Redis keys and their values"""
    print("\n" + "=" * 70)
    print("REDIS KEY INSPECTOR")
    print("=" * 70)
    
    redis_manager = get_redis_manager()
    
    if not redis_manager.is_available():
        print("\n❌ Redis is not available")
        return
    
    redis = redis_manager.get_client()
    
    # Get all TradingAgents keys
    keys = redis.keys('ta:*')
    
    if not keys:
        print("\n📭 No cache keys found in Redis")
        return
    
    print(f"\n📊 Found {len(keys)} Redis keys\n")
    
    for i, key in enumerate(keys, 1):
        print(f"\n{'─' * 70}")
        print(f"Key #{i}: {key}")
        print(f"{'─' * 70}")
        
        # Get TTL
        ttl = redis.ttl(key)
        if ttl == -1:
            ttl_str = "No expiration"
        elif ttl == -2:
            ttl_str = "Expired/doesn't exist"
        else:
            ttl_str = f"{ttl} seconds ({ttl//60} minutes)"
        print(f"TTL: {ttl_str}")
        
        # Get value
        try:
            value = redis.get(key)
            if value:
                # Try to parse as JSON
                try:
                    parsed = json.loads(value)
                    print(f"Type: JSON")
                    print(f"Size: {len(value)} bytes")
                    
                    # Show preview
                    if isinstance(parsed, dict):
                        print(f"Keys: {list(parsed.keys())[:5]}{'...' if len(parsed) > 5 else ''}")
                    elif isinstance(parsed, list):
                        print(f"List length: {len(parsed)}")
                    else:
                        print(f"Value type: {type(parsed).__name__}")
                    
                except json.JSONDecodeError:
                    # Not JSON, show as string preview
                    print(f"Type: String/CSV")
                    print(f"Size: {len(value)} bytes")
                    lines = value.split('\n')
                    print(f"Lines: {len(lines)}")
                    if lines:
                        print(f"First line: {lines[0][:80]}{'...' if len(lines[0]) > 80 else ''}")
            else:
                print("Value: (empty)")
        except Exception as e:
            print(f"Error reading value: {e}")
    
    print("\n" + "=" * 70)


def compare_cache_operations():
    """Compare GET vs SET operations to find key mismatches"""
    print("\n" + "=" * 70)
    print("CACHE OPERATION COMPARISON")
    print("=" * 70)
    
    cache = get_cache()
    stats = cache.get_stats()
    
    print(f"\n📊 Cache Statistics:")
    print(f"   Total Requests: {stats['overall']['total_requests']}")
    print(f"   Redis Available: {stats['redis']['available']}")
    print(f"   Redis Keys: {stats['redis'].get('keys', 0)}")
    print(f"   Redis Hits: {stats['redis']['hits']}")
    print(f"   Redis Misses: {stats['redis']['misses']}")
    
    if stats['redis'].get('keys', 0) > 0 and stats['redis']['hits'] == 0:
        print("\n⚠️  WARNING: Keys exist but no hits!")
        print("   This indicates a cache key mismatch between SET and GET operations.")
        print("\n💡 Recommendations:")
        print("   1. Enable DEBUG logging: Set LOG_LEVEL=DEBUG in .env")
        print("   2. Run your analysis again")
        print("   3. Compare the cache keys in logs:")
        print("      - Look for '🔎 Alpha Vantage GET' lines")
        print("      - Look for '💾 Alpha Vantage SET' lines")
        print("      - Params should be IDENTICAL")
    
    print("\n" + "=" * 70)


def clear_redis_cache():
    """Clear all Redis cache entries"""
    print("\n" + "=" * 70)
    print("CLEAR REDIS CACHE")
    print("=" * 70)
    
    redis_manager = get_redis_manager()
    
    if not redis_manager.is_available():
        print("\n❌ Redis is not available")
        return
    
    count = redis_manager.clear_cache('ta:*')
    print(f"\n✅ Cleared {count} Redis cache entries")
    print("=" * 70)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Cache Key Diagnostic Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Inspect all Redis keys
  python -m tradingagents.utils.cache_debug --inspect
  
  # Compare cache operations
  python -m tradingagents.utils.cache_debug --compare
  
  # Clear Redis cache
  python -m tradingagents.utils.cache_debug --clear
  
  # Run all diagnostics
  python -m tradingagents.utils.cache_debug --all

Note: Run from project root directory
"""
    )
    
    parser.add_argument('--inspect', action='store_true',
                       help='Inspect all Redis keys')
    parser.add_argument('--compare', action='store_true',
                       help='Compare cache statistics')
    parser.add_argument('--clear', action='store_true',
                       help='Clear Redis cache')
    parser.add_argument('--all', action='store_true',
                       help='Run all diagnostics')
    
    args = parser.parse_args()
    
    # Default to --all if no args
    if not any([args.inspect, args.compare, args.clear, args.all]):
        args.all = True
    
    if args.all or args.compare:
        compare_cache_operations()
    
    if args.all or args.inspect:
        inspect_redis_keys()
    
    if args.clear:
        response = input("\n⚠️  Clear all Redis cache? (yes/no): ")
        if response.lower() == 'yes':
            clear_redis_cache()
        else:
            print("Cancelled.")


if __name__ == "__main__":
    main()

