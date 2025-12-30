"""
Test for initial setup and configuration.
Run this first to ensure the environment is properly configured.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all required packages can be imported."""
    print("Testing imports...")
    
    try:
        import google.generativeai as genai
        print("✓ google.generativeai imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import google.generativeai: {e}")
        return False
    
    try:
        import yfinance as yf
        print("✓ yfinance imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import yfinance: {e}")
        return False
    
    try:
        from tenacity import retry
        print("✓ tenacity imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import tenacity: {e}")
        return False
    
    try:
        import chromadb
        print("✓ chromadb imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import chromadb: {e}")
        return False
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        print("✓ langchain_google_genai imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import langchain_google_genai: {e}")
        return False
    
    return True


def test_environment_variables():
    """Test that required environment variables are set."""
    print("\nTesting environment variables...")
    
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if google_api_key:
        print(f"✓ GOOGLE_API_KEY is set (length: {len(google_api_key)})")
    else:
        print("⚠ GOOGLE_API_KEY is not set. You'll need this for Google Gemini.")
        print("  Set it with: export GOOGLE_API_KEY='your-api-key-here'")
    
    return True


def test_config():
    """Test that configuration is properly loaded."""
    print("\nTesting configuration...")
    
    try:
        from tradingagents.default_config import DEFAULT_CONFIG
        print("✓ Default config loaded")
        
        print(f"  LLM Provider: {DEFAULT_CONFIG['llm_provider']}")
        print(f"  Deep Think LLM: {DEFAULT_CONFIG['deep_think_llm']}")
        print(f"  Quick Think LLM: {DEFAULT_CONFIG['quick_think_llm']}")
        print(f"  Cache TTL: {DEFAULT_CONFIG['cache_ttl_seconds']}s")
        print(f"  Data Vendors: {DEFAULT_CONFIG['data_vendors']}")
        
        return True
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        return False


def test_cache_utils():
    """Test cache utilities."""
    print("\nTesting cache utilities...")
    
    try:
        from tradingagents.dataflows.cache_utils import cached, clear_cache
        
        # Test simple caching
        @cached(ttl_seconds=1)
        def test_func(x):
            return x * 2
        
        result1 = test_func(5)
        result2 = test_func(5)
        
        assert result1 == result2 == 10
        print("✓ Cache decorator works")
        
        # Clean up
        clear_cache("test_func")
        print("✓ Cache clearing works")
        
        return True
    except Exception as e:
        print(f"✗ Cache utilities failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rate_limiting():
    """Test rate limiting utilities."""
    print("\nTesting rate limiting...")
    
    try:
        from tradingagents.dataflows.rate_limit_utils import rate_limited
        
        @rate_limited(max_retries=2, multiplier=0.1, max_wait=1)
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"
        print("✓ Rate limiting decorator works")
        
        return True
    except Exception as e:
        print(f"✗ Rate limiting failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory():
    """Test memory with Google embeddings."""
    print("\nTesting memory with embeddings...")
    
    try:
        from tradingagents.agents.utils.memory import FinancialSituationMemory
        from tradingagents.default_config import DEFAULT_CONFIG
        
        test_config = DEFAULT_CONFIG.copy()
        
        # Test with Google embeddings if API key is available
        if os.getenv("GOOGLE_API_KEY"):
            test_config["llm_provider"] = "google"
            memory = FinancialSituationMemory("test_memory", test_config)
            
            # Test adding and retrieving memories
            test_data = [
                ("Market volatility increasing", "Consider defensive positions")
            ]
            memory.add_situations(test_data)
            
            results = memory.get_memories("High market volatility", n_matches=1)
            
            assert len(results) > 0
            print("✓ Memory with Google embeddings works")
        else:
            print("⚠ Skipping Google embeddings test (no API key)")
        
        return True
    except Exception as e:
        print(f"✗ Memory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_yfinance_data():
    """Test Yahoo Finance data fetching."""
    print("\nTesting Yahoo Finance data fetching...")
    
    try:
        from tradingagents.dataflows.y_finance import get_YFin_data_online
        
        # Test with a known stock
        data = get_YFin_data_online("AAPL", "2024-01-01", "2024-01-05")
        
        assert "AAPL" in data
        assert "Date" in data or "No data found" in data
        print("✓ Yahoo Finance data fetching works")
        
        return True
    except Exception as e:
        print(f"✗ Yahoo Finance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all setup tests."""
    print("=" * 60)
    print("TradingAgents Setup Tests")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Environment Variables", test_environment_variables),
        ("Configuration", test_config),
        ("Cache Utilities", test_cache_utils),
        ("Rate Limiting", test_rate_limiting),
        ("Memory System", test_memory),
        ("Yahoo Finance", test_yfinance_data),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! System is ready to use.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

