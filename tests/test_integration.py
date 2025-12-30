"""
Integration test for the full TradingAgents system.
This test runs the complete agent workflow.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_full_workflow_google():
    """Test the full workflow with Google Gemini."""
    print("\n" + "=" * 60)
    print("Testing Full Workflow with Google Gemini")
    print("=" * 60)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠ GOOGLE_API_KEY not set. Skipping this test.")
        print("  Set it with: export GOOGLE_API_KEY='your-api-key-here'")
        return None
    
    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # Create a config with Google Gemini
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = "google"
        config["deep_think_llm"] = "gemini-1.5-pro"
        config["quick_think_llm"] = "gemini-1.5-flash"
        config["max_debate_rounds"] = 1
        config["max_risk_discuss_rounds"] = 1
        
        # Use only news analyst for faster testing
        config["data_vendors"]["news_data"] = "google"
        
        print("\nConfiguration:")
        print(f"  Provider: {config['llm_provider']}")
        print(f"  Deep Think: {config['deep_think_llm']}")
        print(f"  Quick Think: {config['quick_think_llm']}")
        print(f"  Data Vendors: {config['data_vendors']}")
        
        print("\nInitializing TradingAgentsGraph...")
        ta = TradingAgentsGraph(
            selected_analysts=["news"],  # Just test news for speed
            debug=False,
            config=config
        )
        
        print("✓ Graph initialized successfully")
        
        print("\nRunning propagation for AAPL on 2024-05-10...")
        print("(This may take a few minutes...)")
        
        _, decision = ta.propagate("AAPL", "2024-05-10")
        
        print(f"\n✓ Propagation completed!")
        print(f"Decision: {decision}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Full workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cache_persistence():
    """Test that cache persists across runs."""
    print("\n" + "=" * 60)
    print("Testing Cache Persistence")
    print("=" * 60)
    
    try:
        from tradingagents.dataflows.y_finance import get_YFin_data_online
        from tradingagents.dataflows.cache_utils import get_cache_path, is_cache_valid, get_cache_key
        import time
        
        ticker = "MSFT"
        start_date = "2024-01-01"
        end_date = "2024-01-05"
        
        print(f"Fetching {ticker} data...")
        
        # First call
        data1 = get_YFin_data_online(ticker, start_date, end_date)
        
        # Check cache exists
        cache_key = get_cache_key(ticker, start_date, end_date)
        cache_file = get_cache_path("get_YFin_data_online", cache_key)
        
        if cache_file.exists():
            print(f"✓ Cache file created at: {cache_file}")
        else:
            print(f"⚠ Cache file not found at: {cache_file}")
            return False
        
        # Check cache is valid
        if is_cache_valid(cache_file, 3600):
            print("✓ Cache is valid (TTL not expired)")
        else:
            print("⚠ Cache is not valid")
            return False
        
        # Second call should be faster
        start_time = time.time()
        data2 = get_YFin_data_online(ticker, start_date, end_date)
        elapsed = time.time() - start_time
        
        print(f"✓ Second call completed in {elapsed:.3f}s (from cache)")
        
        assert data1 == data2
        print("✓ Cache data matches original")
        
        return True
        
    except Exception as e:
        print(f"✗ Cache persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rate_limiting_with_retry():
    """Test that rate limiting retries work correctly."""
    print("\n" + "=" * 60)
    print("Testing Rate Limiting with Retry")
    print("=" * 60)
    
    try:
        from tradingagents.dataflows.rate_limit_utils import rate_limited
        
        call_count = [0]
        
        @rate_limited(max_retries=3, multiplier=0.1, max_wait=1)
        def flaky_function():
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("Simulated rate limit error")
            return "success"
        
        result = flaky_function()
        
        print(f"✓ Function succeeded after {call_count[0]} attempts")
        assert result == "success"
        assert call_count[0] == 3
        
        return True
        
    except Exception as e:
        print(f"✗ Rate limiting test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory_persistence():
    """Test memory system with embeddings."""
    print("\n" + "=" * 60)
    print("Testing Memory Persistence")
    print("=" * 60)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠ GOOGLE_API_KEY not set. Skipping this test.")
        return None
    
    try:
        from tradingagents.agents.utils.memory import FinancialSituationMemory
        from tradingagents.default_config import DEFAULT_CONFIG
        
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = "google"
        
        print("Creating memory with Google embeddings...")
        memory = FinancialSituationMemory("integration_test_memory", config)
        
        # Add test data
        test_situations = [
            ("High inflation with rising rates", "Shift to defensive sectors"),
            ("Tech sector volatility increasing", "Reduce growth stock exposure"),
            ("Strong dollar impacting emerging markets", "Hedge currency exposure"),
        ]
        
        print("Adding situations to memory...")
        memory.add_situations(test_situations)
        
        # Query memory
        print("Querying memory...")
        query = "Market showing high volatility in technology stocks"
        results = memory.get_memories(query, n_matches=2)
        
        print(f"\nQuery: {query}")
        print(f"Found {len(results)} matches:")
        for i, result in enumerate(results, 1):
            print(f"\n  Match {i}:")
            print(f"    Situation: {result['matched_situation'][:50]}...")
            print(f"    Recommendation: {result['recommendation'][:50]}...")
            print(f"    Similarity: {result['similarity_score']:.3f}")
        
        assert len(results) > 0
        print("\n✓ Memory system works correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Memory persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("TradingAgents Integration Tests")
    print("=" * 60)
    print("\nThese tests run the full system and make actual API calls.")
    print("Make sure you have set GOOGLE_API_KEY in your environment.\n")
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠ GOOGLE_API_KEY not set!")
        print("  Set it with: export GOOGLE_API_KEY='your-api-key-here'")
        print("\nMost tests will be skipped without this key.\n")
    
    tests = [
        ("Cache Persistence", test_cache_persistence),
        ("Rate Limiting with Retry", test_rate_limiting_with_retry),
        ("Memory Persistence", test_memory_persistence),
        ("Full Workflow (Google)", test_full_workflow_google),
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
        if result is None:
            print(f"⊘ SKIP: {name}")
        elif result:
            print(f"✓ PASS: {name}")
        else:
            print(f"✗ FAIL: {name}")
    
    total = len([r for _, r in results if r is not None])
    passed = sum(1 for _, r in results if r is True)
    skipped = sum(1 for _, r in results if r is None)
    
    print(f"\nPassed: {passed}/{total}")
    if skipped > 0:
        print(f"Skipped: {skipped}")
    
    if passed == total:
        print("\n✓ All integration tests passed!")
        return 0
    elif total == 0:
        print("\n⊘ All tests were skipped (missing API key?)")
        return 2
    else:
        print(f"\n⚠ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

