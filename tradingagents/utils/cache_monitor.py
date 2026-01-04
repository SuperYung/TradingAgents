"""
Cache monitoring and management utilities
CLI tool for monitoring cache health, statistics, and cleanup
"""

import argparse
import logging
from typing import Optional

from tradingagents.dataflows.cache import get_cache
from tradingagents.config import CacheConfig

logger = logging.getLogger(__name__)


def print_banner():
    """Print banner"""
    print("\n" + "=" * 70)
    print("TradingAgents Cache Monitor")
    print("=" * 70 + "\n")


def show_stats():
    """Show cache statistics"""
    print_banner()
    
    # Show configuration
    print("📋 Cache Configuration:")
    print("-" * 70)
    CacheConfig.print_config()
    
    # Show statistics
    cache = get_cache()
    cache.print_stats()


def clear_cache(pattern: str = "*"):
    """Clear cache entries matching pattern"""
    print_banner()
    
    print(f"🧹 Clearing cache entries matching: {pattern}")
    print("-" * 70)
    
    cache = get_cache()
    result = cache.clear_pattern(pattern)
    
    print(f"\n✅ Cleared:")
    print(f"   Redis: {result['redis']} entries")
    print(f"   File: {result['file']} entries")
    print(f"   Total: {result['redis'] + result['file']} entries\n")


def test_cache():
    """Test cache functionality"""
    print_banner()
    
    print("🧪 Testing cache functionality...")
    print("-" * 70)
    
    cache = get_cache()
    
    # Test 1: Set and Get
    print("\n1. Testing SET and GET:")
    test_data = {"symbol": "AAPL", "price": 150.0, "timestamp": "2025-01-04"}
    
    cache.set('stock_quote', test_data, symbol='AAPL')
    print("   ✅ SET: stock_quote for AAPL")
    
    cached = cache.get('stock_quote', symbol='AAPL')
    if cached == test_data:
        print("   ✅ GET: Retrieved correct data")
    else:
        print("   ❌ GET: Data mismatch!")
    
    # Test 2: Cache miss
    print("\n2. Testing cache MISS:")
    missed = cache.get('stock_quote', symbol='NONEXISTENT')
    if missed is None:
        print("   ✅ Cache miss returned None as expected")
    else:
        print("   ❌ Cache miss returned data!")
    
    # Test 3: Delete
    print("\n3. Testing DELETE:")
    cache.delete('stock_quote', symbol='AAPL')
    deleted_check = cache.get('stock_quote', symbol='AAPL')
    if deleted_check is None:
        print("   ✅ DELETE: Entry removed successfully")
    else:
        print("   ❌ DELETE: Entry still exists!")
    
    # Show final stats
    print("\n4. Final Statistics:")
    cache.print_stats()
    
    print("✅ Cache testing complete!\n")


def health_check():
    """Check cache health"""
    print_banner()
    
    print("🏥 Cache Health Check")
    print("-" * 70)
    
    cache = get_cache()
    stats = cache.get_stats()
    
    # Check Redis
    redis_status = "✅ Healthy" if stats['redis']['available'] else "⚠️  Unavailable (using file cache)"
    print(f"\n🔴 Redis: {redis_status}")
    
    if stats['redis']['available']:
        print(f"   Keys: {stats['redis'].get('keys', 0)}")
        print(f"   Memory: {stats['redis'].get('memory', 'N/A')}")
        print(f"   Uptime: {stats['redis'].get('uptime_days', 0)} days")
    
    # Check File Cache
    file_status = "✅ Healthy" if stats['file']['enabled'] else "❌ Disabled"
    print(f"\n📁 File Cache: {file_status}")
    print(f"   Entries: {stats['file']['total_entries']}")
    print(f"   Size: {stats['file']['total_size_mb']} MB")
    print(f"   Hit Rate: {stats['file']['hit_rate']}%")
    
    # Overall health
    print(f"\n🎯 Overall:")
    print(f"   Mode: {stats['mode']}")
    print(f"   Total Requests: {stats['overall']['total_requests']}")
    print(f"   Overall Hit Rate: {stats['overall']['hit_rate']}%")
    
    # Recommendations
    print("\n💡 Recommendations:")
    if not stats['redis']['available']:
        print("   • Consider enabling Redis for better performance")
    
    if stats['file']['total_size_mb'] > 1000:
        print("   • File cache is large (>1GB), consider cleanup")
    
    if stats['overall']['total_requests'] > 100 and stats['overall']['hit_rate'] < 50:
        print("   • Low hit rate, consider increasing TTL values")
    
    print()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="TradingAgents Cache Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show cache statistics
  python -m tradingagents.utils.cache_monitor --stats
  
  # Clear all cache
  python -m tradingagents.utils.cache_monitor --clear
  
  # Clear specific pattern
  python -m tradingagents.utils.cache_monitor --clear --pattern "AAPL*"
  
  # Test cache functionality
  python -m tradingagents.utils.cache_monitor --test
  
  # Health check
  python -m tradingagents.utils.cache_monitor --health
"""
    )
    
    parser.add_argument('--stats', action='store_true',
                       help='Show cache statistics')
    parser.add_argument('--clear', action='store_true',
                       help='Clear cache entries')
    parser.add_argument('--pattern', type=str, default='*',
                       help='Pattern for clearing (default: *)')
    parser.add_argument('--test', action='store_true',
                       help='Test cache functionality')
    parser.add_argument('--health', action='store_true',
                       help='Check cache health')
    parser.add_argument('--verbose', action='store_true',
                       help='Verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Execute commands
    if args.stats:
        show_stats()
    elif args.clear:
        clear_cache(args.pattern)
    elif args.test:
        test_cache()
    elif args.health:
        health_check()
    else:
        # Default: show stats
        show_stats()


if __name__ == "__main__":
    main()

