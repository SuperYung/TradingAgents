"""
Example: Using TradingAgents with Google Gemini (Free Tier)

This example demonstrates the migrated system using:
- Google Gemini Pro for LLM
- Yahoo Finance for stock data
- Caching for performance
- Rate limiting for reliability
"""

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.dataflows.cache_utils import clear_cache
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


def example_basic_usage():
    """Basic example using default configuration."""
    print("=" * 60)
    print("Example 1: Basic Usage with Google Gemini (Free)")
    print("=" * 60)
    
    # Check API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠ GOOGLE_API_KEY not set!")
        print("Get your free key from: https://makersuite.google.com/app/apikey")
        return
    
    # Use default config (already set to Google Gemini + Yahoo Finance)
    config = DEFAULT_CONFIG.copy()
    
    print("\nConfiguration:")
    print(f"  LLM Provider: {config['llm_provider']}")
    print(f"  Deep Think: {config['deep_think_llm']}")
    print(f"  Quick Think: {config['quick_think_llm']}")
    print(f"  Cache TTL: {config['cache_ttl_seconds']}s")
    print(f"  Data Vendors: {config['data_vendors']}")
    
    # Initialize trading agents
    print("\nInitializing TradingAgentsGraph...")
    ta = TradingAgentsGraph(
        selected_analysts=["market", "news"],  # Use fewer for faster demo
        debug=True,
        config=config
    )
    
    # Run analysis
    ticker = "AAPL"
    date = "2024-05-10"
    
    print(f"\nAnalyzing {ticker} on {date}...")
    print("(This may take 1-2 minutes for the first run...)\n")
    
    _, decision = ta.propagate(ticker, date)
    
    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print("=" * 60)
    print(f"Decision: {decision}")


def example_custom_config():
    """Example with custom configuration."""
    print("\n" + "=" * 60)
    print("Example 2: Custom Configuration")
    print("=" * 60)
    
    config = DEFAULT_CONFIG.copy()
    
    # Customize settings
    config["max_debate_rounds"] = 2  # More thorough debate
    config["cache_ttl_seconds"] = 7200  # 2-hour cache
    config["rate_limit_max_retries"] = 3  # Fewer retries
    
    print("\nCustom Configuration:")
    print(f"  Debate Rounds: {config['max_debate_rounds']}")
    print(f"  Cache TTL: {config['cache_ttl_seconds']}s")
    print(f"  Max Retries: {config['rate_limit_max_retries']}")
    
    ta = TradingAgentsGraph(
        selected_analysts=["market", "news"],
        debug=False,  # Less verbose
        config=config
    )
    
    _, decision = ta.propagate("MSFT", "2024-05-10")
    print(f"\nDecision for MSFT: {decision}")


def example_cache_demo():
    """Demonstrate caching performance."""
    print("\n" + "=" * 60)
    print("Example 3: Cache Performance Demo")
    print("=" * 60)
    
    from tradingagents.dataflows.y_finance import get_YFin_data_online
    import time
    
    ticker = "TSLA"
    start_date = "2024-01-01"
    end_date = "2024-01-31"
    
    print(f"\nFetching {ticker} data...")
    
    # First call - not cached
    print("First call (uncached):")
    start_time = time.time()
    data1 = get_YFin_data_online(ticker, start_date, end_date)
    elapsed1 = time.time() - start_time
    print(f"  Time: {elapsed1:.3f}s")
    print(f"  Data size: {len(data1)} chars")
    
    # Second call - cached
    print("\nSecond call (cached):")
    start_time = time.time()
    data2 = get_YFin_data_online(ticker, start_date, end_date)
    elapsed2 = time.time() - start_time
    print(f"  Time: {elapsed2:.3f}s")
    print(f"  Speedup: {elapsed1/elapsed2:.1f}x faster!")
    
    assert data1 == data2, "Cache data should match"
    print("\n✓ Cache working correctly!")


def example_memory_demo():
    """Demonstrate memory system with embeddings."""
    print("\n" + "=" * 60)
    print("Example 4: Memory System Demo")
    print("=" * 60)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠ GOOGLE_API_KEY required for embeddings")
        return
    
    from tradingagents.agents.utils.memory import FinancialSituationMemory
    
    config = DEFAULT_CONFIG.copy()
    
    print("\nCreating memory with Google embeddings...")
    memory = FinancialSituationMemory("demo_memory", config)
    
    # Add example situations
    situations = [
        (
            "High inflation with rising interest rates",
            "Shift to defensive sectors like utilities and consumer staples"
        ),
        (
            "Tech sector showing high volatility with selling pressure",
            "Reduce growth stock exposure, focus on profitable tech companies"
        ),
        (
            "Strong dollar impacting emerging markets",
            "Hedge currency exposure, reduce EM allocation"
        ),
    ]
    
    print("Adding situations to memory...")
    memory.add_situations(situations)
    
    # Query memory
    query = "Market showing technology stock volatility"
    print(f"\nQuerying: '{query}'")
    
    results = memory.get_memories(query, n_matches=2)
    
    print(f"\nFound {len(results)} matches:")
    for i, result in enumerate(results, 1):
        print(f"\nMatch {i}:")
        print(f"  Similarity: {result['similarity_score']:.3f}")
        print(f"  Situation: {result['matched_situation'][:60]}...")
        print(f"  Recommendation: {result['recommendation'][:60]}...")


def example_multi_ticker():
    """Analyze multiple tickers."""
    print("\n" + "=" * 60)
    print("Example 5: Multi-Ticker Analysis")
    print("=" * 60)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠ GOOGLE_API_KEY required")
        return
    
    config = DEFAULT_CONFIG.copy()
    config["max_debate_rounds"] = 1  # Faster
    
    ta = TradingAgentsGraph(
        selected_analysts=["market"],  # Just technical for speed
        debug=False,
        config=config
    )
    
    tickers = ["AAPL", "MSFT", "GOOGL"]
    date = "2024-05-10"
    
    print(f"\nAnalyzing {len(tickers)} tickers on {date}...")
    print("(With caching, repeated analyses are much faster)\n")
    
    results = {}
    for ticker in tickers:
        print(f"Analyzing {ticker}...", end=" ")
        _, decision = ta.propagate(ticker, date)
        results[ticker] = decision
        print(f"Done: {decision}")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    for ticker, decision in results.items():
        print(f"{ticker:6s}: {decision}")


def example_cache_management():
    """Demonstrate cache management."""
    print("\n" + "=" * 60)
    print("Example 6: Cache Management")
    print("=" * 60)
    
    from tradingagents.dataflows.cache_utils import clear_cache
    from pathlib import Path
    
    config = DEFAULT_CONFIG.copy()
    cache_dir = Path(config["cache_dir"])
    
    print(f"\nCache directory: {cache_dir}")
    
    if cache_dir.exists():
        # Count cache files
        cache_files = list(cache_dir.rglob("*.json"))
        print(f"Current cache files: {len(cache_files)}")
        
        if cache_files:
            # Show size
            total_size = sum(f.stat().st_size for f in cache_files)
            print(f"Total cache size: {total_size / 1024:.1f} KB")
            
            # Clear specific function cache
            print("\nClearing 'get_YFin_data_online' cache...")
            clear_cache("get_YFin_data_online")
            
            # Check again
            cache_files_after = list(cache_dir.rglob("*.json"))
            print(f"Cache files after clear: {len(cache_files_after)}")
    else:
        print("No cache directory yet (run some analyses first)")


def main():
    """Run all examples."""
    print("=" * 60)
    print("TradingAgents Examples - Free Tier Edition")
    print("=" * 60)
    print("\nThese examples demonstrate the migrated system using:")
    print("  ✓ Google Gemini Pro (free)")
    print("  ✓ Yahoo Finance (free)")
    print("  ✓ Caching (fast)")
    print("  ✓ Rate limiting (reliable)")
    print()
    
    # Check API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠ GOOGLE_API_KEY not set!")
        print("\nTo run these examples:")
        print("1. Get your free API key: https://makersuite.google.com/app/apikey")
        print("2. Set it: export GOOGLE_API_KEY='your-key-here'")
        print("3. Run this script again")
        return
    
    try:
        # Example 3: Cache demo (fast)
        example_cache_demo()
        
        # Example 4: Memory demo (fast)
        example_memory_demo()
        
        # Example 6: Cache management (fast)
        example_cache_management()
        
        # Comment out slower examples for quick demo
        # Uncomment to run full examples:
        
        # example_basic_usage()
        # example_custom_config()
        # example_multi_ticker()
        
        print("\n" + "=" * 60)
        print("Examples Complete!")
        print("=" * 60)
        print("\nTo run the full trading analysis, uncomment the")
        print("slower examples in main() or run:")
        print("  python main.py")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("1. Check GOOGLE_API_KEY is set")
        print("2. Verify internet connection")
        print("3. Run: python tests/test_setup.py")


if __name__ == "__main__":
    main()

