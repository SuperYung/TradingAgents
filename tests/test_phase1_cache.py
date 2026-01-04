"""
Test suite for Phase 1 Cache Integration
Validates Redis, File Cache, and IntegratedCache functionality
"""

import os
import sys
import time
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all modules can be imported"""
    print("=" * 70)
    print("TEST 1: Module Imports")
    print("=" * 70)
    
    try:
        from tradingagents.config import RedisManager, CacheConfig
        from tradingagents.config import get_redis_manager, get_redis_client
        from tradingagents.dataflows.cache import IntegratedCache, get_cache
        from tradingagents.dataflows.cache import EnhancedFileCache, get_file_cache
        
        print("✅ All modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_cache_config():
    """Test CacheConfig functionality"""
    print("\n" + "=" * 70)
    print("TEST 2: CacheConfig")
    print("=" * 70)
    
    try:
        from tradingagents.config import CacheConfig
        
        # Test TTL retrieval
        ttl = CacheConfig.get_ttl('stock_quote')
        assert ttl > 0, "TTL should be positive"
        print(f"✅ get_ttl('stock_quote') = {ttl}s")
        
        # Test all TTLs
        all_ttls = CacheConfig.get_all_ttls()
        assert 'stock_quote' in all_ttls
        assert 'fundamentals' in all_ttls
        print(f"✅ get_all_ttls() returned {len(all_ttls)} TTL configs")
        
        # Test configs
        redis_conf = CacheConfig.get_redis_config()
        assert 'enabled' in redis_conf
        print(f"✅ Redis config: enabled={redis_conf['enabled']}")
        
        file_conf = CacheConfig.get_file_cache_config()
        assert 'enabled' in file_conf
        print(f"✅ File cache config: enabled={file_conf['enabled']}")
        
        print("\n📋 Configuration Summary:")
        CacheConfig.print_config()
        
        return True
    except Exception as e:
        print(f"❌ CacheConfig test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_redis_manager():
    """Test RedisManager functionality"""
    print("\n" + "=" * 70)
    print("TEST 3: RedisManager")
    print("=" * 70)
    
    try:
        from tradingagents.config import get_redis_manager
        
        manager = get_redis_manager()
        print(f"✅ RedisManager initialized")
        
        # Check availability
        available = manager.is_available()
        print(f"📊 Redis available: {available}")
        
        if available:
            # Test client
            client = manager.get_client()
            assert client is not None
            print("✅ Redis client retrieved")
            
            # Test stats
            stats = manager.get_stats()
            print(f"✅ Redis stats: {stats.get('keys', 0)} keys, {stats.get('memory', 'N/A')} memory")
        else:
            print("⚠️  Redis not available (will use file cache)")
        
        return True
    except Exception as e:
        print(f"❌ RedisManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_cache():
    """Test EnhancedFileCache functionality"""
    print("\n" + "=" * 70)
    print("TEST 4: EnhancedFileCache")
    print("=" * 70)
    
    try:
        from tradingagents.dataflows.cache import get_file_cache
        
        # Use temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            from tradingagents.dataflows.cache.enhanced_file_cache import EnhancedFileCache
            cache = EnhancedFileCache(base_dir=tmpdir)
            print(f"✅ File cache initialized in {tmpdir}")
            
            # Test SET
            test_data = {'symbol': 'TEST', 'price': 100.0}
            success = cache.set('test_cache_key', test_data, 'stock_quote')
            assert success, "Cache set should succeed"
            print("✅ Cache SET successful")
            
            # Test GET (should hit)
            retrieved = cache.get('test_cache_key', 'stock_quote')
            assert retrieved == test_data, "Retrieved data should match"
            print("✅ Cache GET successful (HIT)")
            
            # Test GET (should miss - different key)
            missed = cache.get('nonexistent_key', 'stock_quote')
            assert missed is None, "Nonexistent key should return None"
            print("✅ Cache GET successful (MISS)")
            
            # Test DELETE
            deleted = cache.delete('test_cache_key', 'stock_quote')
            assert deleted, "Delete should succeed"
            
            # Verify deleted
            after_delete = cache.get('test_cache_key', 'stock_quote')
            assert after_delete is None, "Deleted key should return None"
            print("✅ Cache DELETE successful")
            
            # Test stats
            stats = cache.get_stats()
            assert 'total_entries' in stats
            print(f"✅ Cache stats: {stats['hits']} hits, {stats['misses']} misses")
        
        return True
    except Exception as e:
        print(f"❌ File cache test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integrated_cache():
    """Test IntegratedCache functionality"""
    print("\n" + "=" * 70)
    print("TEST 5: IntegratedCache")
    print("=" * 70)
    
    try:
        from tradingagents.dataflows.cache import get_cache
        
        cache = get_cache()
        print("✅ IntegratedCache initialized")
        print(f"📊 Cache mode: {cache.mode}")
        
        # Test SET
        test_data = {'symbol': 'AAPL', 'price': 150.0, 'timestamp': '2025-01-04'}
        success = cache.set('stock_quote', test_data, symbol='AAPL')
        assert success, "Cache set should succeed"
        print("✅ Integrated cache SET successful")
        
        # Test GET (should hit)
        retrieved = cache.get('stock_quote', symbol='AAPL')
        assert retrieved == test_data, "Retrieved data should match"
        print("✅ Integrated cache GET successful (HIT)")
        
        # Test GET (should miss)
        missed = cache.get('stock_quote', symbol='NONEXISTENT')
        assert missed is None, "Nonexistent should return None"
        print("✅ Integrated cache GET successful (MISS)")
        
        # Test DELETE
        deleted = cache.delete('stock_quote', symbol='AAPL')
        print("✅ Integrated cache DELETE successful")
        
        # Test stats
        stats = cache.get_stats()
        print(f"\n📊 Integrated Cache Statistics:")
        cache.print_stats()
        
        return True
    except Exception as e:
        print(f"❌ Integrated cache test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_provider_integration():
    """Test that providers can use the cache"""
    print("\n" + "=" * 70)
    print("TEST 6: Provider Integration")
    print("=" * 70)
    
    try:
        # Test Alpha Vantage common imports
        from tradingagents.dataflows import alpha_vantage_common
        print("✅ Alpha Vantage module imports cache")
        
        # Test Yahoo Finance imports
        from tradingagents.dataflows import y_finance
        print("✅ Yahoo Finance module imports cache")
        
        # Verify cache is accessible
        assert hasattr(alpha_vantage_common, 'cache'), "Alpha Vantage should have cache"
        assert hasattr(y_finance, 'cache'), "Yahoo Finance should have cache"
        print("✅ Both providers have cache instances")
        
        return True
    except Exception as e:
        print(f"❌ Provider integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cache_monitor():
    """Test cache monitor utility"""
    print("\n" + "=" * 70)
    print("TEST 7: Cache Monitor Utility")
    print("=" * 70)
    
    try:
        from tradingagents.utils import cache_monitor
        print("✅ Cache monitor module imported")
        
        # Test that functions exist
        assert hasattr(cache_monitor, 'show_stats')
        assert hasattr(cache_monitor, 'clear_cache')
        assert hasattr(cache_monitor, 'test_cache')
        assert hasattr(cache_monitor, 'health_check')
        print("✅ All monitor functions available")
        
        return True
    except Exception as e:
        print(f"❌ Cache monitor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "=" * 70)
    print("PHASE 1 CACHE INTEGRATION TEST SUITE")
    print("=" * 70)
    
    tests = [
        ("Module Imports", test_imports),
        ("CacheConfig", test_cache_config),
        ("RedisManager", test_redis_manager),
        ("EnhancedFileCache", test_file_cache),
        ("IntegratedCache", test_integrated_cache),
        ("Provider Integration", test_provider_integration),
        ("Cache Monitor", test_cache_monitor),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "=" * 70)
    print(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 All tests passed! Cache integration is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

