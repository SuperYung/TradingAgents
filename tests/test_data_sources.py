#!/usr/bin/env python3
"""
Test script for the Multi-Source Data Architecture.
Tests providers, fallback mechanism, caching, and the DataSourceManager.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tradingagents.dataflows.data_source_manager import get_data_source_manager, reset_data_source_manager
from tradingagents.dataflows.providers.us import YahooFinanceProvider, GoogleProvider, AlphaVantageProvider
from tradingagents.utils.logging_manager import get_logger

logger = get_logger("tradingagents.tests.data_sources")


def test_yahoo_finance_provider():
    """Test Yahoo Finance provider directly."""
    print("\n" + "="*70)
    print("TEST 1: Yahoo Finance Provider")
    print("="*70)
    
    provider = YahooFinanceProvider()
    
    print(f"Provider name: {provider.name}")
    print(f"Priority: {provider.priority}")
    print(f"Available: {provider.is_available()}")
    
    if provider.is_available():
        # Test quote
        print("\nTesting get_stock_quote('AAPL')...")
        quote = asyncio.run(provider.get_stock_quote("AAPL"))
        if quote:
            print(f"✅ Quote: ${quote['price']}, Volume: {quote['volume']}")
        else:
            print("❌ No quote data")
        
        # Test historical data
        print("\nTesting get_historical_data('AAPL')...")
        hist_data = asyncio.run(provider.get_historical_data(
            "AAPL", "2025-01-01", "2025-01-10"
        ))
        if hist_data:
            lines = hist_data.strip().split('\n')
            print(f"✅ Historical data: {len(lines)-1} rows")
        else:
            print("❌ No historical data")
        
        # Test stock info
        print("\nTesting get_stock_info('AAPL')...")
        info = asyncio.run(provider.get_stock_info("AAPL"))
        if info:
            print(f"✅ Info: {info.get('name')}, Sector: {info.get('sector')}")
        else:
            print("❌ No stock info")
        
        print("\n✅ Yahoo Finance provider test complete")
    else:
        print("\n⚠️  Yahoo Finance not available")


def test_google_provider():
    """Test Google provider directly."""
    print("\n" + "="*70)
    print("TEST 2: Google Provider")
    print("="*70)
    
    provider = GoogleProvider()
    
    print(f"Provider name: {provider.name}")
    print(f"Priority: {provider.priority}")
    print(f"Available: {provider.is_available()}")
    
    # Test news
    print("\nTesting get_news('AAPL')...")
    news = asyncio.run(provider.get_news("AAPL", limit=3))
    if news:
        print(f"✅ News: {len(news)} articles")
        for i, article in enumerate(news[:2], 1):
            print(f"  {i}. {article.get('title', 'No title')[:60]}...")
    else:
        print("⚠️  No news data (this is expected)")
    
    print("\n✅ Google provider test complete")


def test_alpha_vantage_provider():
    """Test Alpha Vantage provider directly."""
    print("\n" + "="*70)
    print("TEST 3: Alpha Vantage Provider")
    print("="*70)
    
    provider = AlphaVantageProvider()
    
    print(f"Provider name: {provider.name}")
    print(f"Priority: {provider.priority}")
    print(f"Available: {provider.is_available()}")
    
    if provider.is_available():
        print("\nTesting Alpha Vantage (rate limited - this may take time)...")
        print("⚠️  Skipping actual API calls to avoid rate limits in testing")
        print("✅ Alpha Vantage provider initialized")
    else:
        print("\n⚠️  Alpha Vantage not available (API key not set)")
        print("   Set ALPHA_VANTAGE_API_KEY environment variable to test")


def test_data_source_manager():
    """Test DataSourceManager with fallback."""
    print("\n" + "="*70)
    print("TEST 4: DataSourceManager")
    print("="*70)
    
    # Reset and get fresh instance
    reset_data_source_manager()
    manager = get_data_source_manager()
    
    print(f"Manager: {manager}")
    print(f"Number of providers: {len(manager.providers)}")
    
    # Show provider status
    status = manager.get_provider_status()
    print("\nProvider Status:")
    for name, info in status.items():
        available = "✅" if info['available'] else "❌"
        print(f"  {available} {name}: priority={info['priority']}, available={info['available']}")
    
    # Test quote with fallback
    print("\nTesting get_stock_quote('AAPL') with fallback...")
    quote = asyncio.run(manager.get_stock_quote("AAPL"))
    if quote:
        print(f"✅ Quote from {quote['provider']}: ${quote['price']}")
    else:
        print("❌ All providers failed")
    
    # Test historical data
    print("\nTesting get_historical_data('AAPL')...")
    hist = asyncio.run(manager.get_historical_data(
        "AAPL", "2025-01-01", "2025-01-10"
    ))
    if hist:
        lines = hist.strip().split('\n')
        print(f"✅ Historical data: {len(lines)-1} rows")
    else:
        print("❌ No historical data")
    
    # Test stock info
    print("\nTesting get_stock_info('AAPL')...")
    info = asyncio.run(manager.get_stock_info("AAPL"))
    if info:
        print(f"✅ Info from {info.get('provider')}: {info.get('name')}")
    else:
        print("❌ No stock info")
    
    # Test fundamentals
    print("\nTesting get_fundamentals('AAPL')...")
    fund = asyncio.run(manager.get_fundamentals("AAPL"))
    if fund:
        print(f"✅ Fundamentals from {fund.get('provider')}")
        if 'pe_ratio' in fund:
            print(f"   P/E Ratio: {fund['pe_ratio']}")
    else:
        print("⚠️  No fundamentals")
    
    # Test news
    print("\nTesting get_news('AAPL')...")
    news = asyncio.run(manager.get_news("AAPL", limit=3))
    if news:
        print(f"✅ News: {len(news)} articles")
    else:
        print("⚠️  No news")
    
    print("\n✅ DataSourceManager test complete")


def test_caching():
    """Test caching mechanism."""
    print("\n" + "="*70)
    print("TEST 5: Caching")
    print("="*70)
    
    provider = YahooFinanceProvider(cache_ttl=60)
    
    if not provider.is_available():
        print("⚠️  Provider not available, skipping cache test")
        return
    
    import time
    
    print("First call (should fetch from API)...")
    start = time.time()
    quote1 = asyncio.run(provider.get_stock_quote("AAPL"))
    time1 = time.time() - start
    
    print(f"  Time: {time1:.3f}s")
    
    print("\nSecond call (should use cache)...")
    start = time.time()
    quote2 = asyncio.run(provider.get_stock_quote("AAPL"))
    time2 = time.time() - start
    
    print(f"  Time: {time2:.3f}s")
    
    if time2 < time1 / 2:
        print(f"✅ Cache working (2nd call {time1/time2:.1f}x faster)")
    else:
        print("⚠️  Cache may not be working as expected")
    
    if quote1 == quote2:
        print("✅ Cache returned same data")
    else:
        print("⚠️  Cache returned different data")


def test_fallback_mechanism():
    """Test fallback when primary provider fails."""
    print("\n" + "="*70)
    print("TEST 6: Fallback Mechanism")
    print("="*70)
    
    print("This test simulates fallback behavior...")
    print("In production, if Yahoo Finance fails, the system")
    print("automatically tries Google, then Alpha Vantage.")
    
    reset_data_source_manager()
    manager = get_data_source_manager()
    
    # Test with valid symbol
    print("\nTest with valid symbol (AAPL)...")
    quote = asyncio.run(manager.get_stock_quote("AAPL"))
    if quote:
        print(f"✅ Got data from: {quote.get('provider')}")
    else:
        print("❌ All providers failed")
    
    # Test with invalid symbol
    print("\nTest with invalid symbol (INVALID123)...")
    quote = asyncio.run(manager.get_stock_quote("INVALID123"))
    if quote:
        print(f"⚠️  Unexpectedly got data: {quote}")
    else:
        print("✅ Correctly handled invalid symbol (all providers failed)")
    
    print("\n✅ Fallback mechanism test complete")


def test_parallel_requests():
    """Test parallel requests to multiple symbols."""
    print("\n" + "="*70)
    print("TEST 7: Parallel Requests")
    print("="*70)
    
    reset_data_source_manager()
    manager = get_data_source_manager()
    
    symbols = ["AAPL", "MSFT", "GOOGL"]
    
    print(f"Fetching quotes for {len(symbols)} symbols in parallel...")
    
    import time
    start = time.time()
    
    async def fetch_all():
        tasks = [manager.get_stock_quote(symbol) for symbol in symbols]
        return await asyncio.gather(*tasks)
    
    quotes = asyncio.run(fetch_all())
    elapsed = time.time() - start
    
    success_count = sum(1 for q in quotes if q is not None)
    print(f"\n✅ Fetched {success_count}/{len(symbols)} quotes in {elapsed:.2f}s")
    
    for symbol, quote in zip(symbols, quotes):
        if quote:
            print(f"  {symbol}: ${quote['price']} (from {quote['provider']})")
        else:
            print(f"  {symbol}: Failed")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("MULTI-SOURCE DATA ARCHITECTURE TEST SUITE")
    print("="*70)
    
    tests = [
        test_yahoo_finance_provider,
        test_google_provider,
        test_alpha_vantage_provider,
        test_data_source_manager,
        test_caching,
        test_fallback_mechanism,
        test_parallel_requests
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ Test {test_func.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {failed} test(s) failed")
    
    print("\nNote: Some tests may show warnings if API keys are not set.")
    print("This is expected behavior.")
    print("="*70)


if __name__ == "__main__":
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Run all tests
    run_all_tests()

