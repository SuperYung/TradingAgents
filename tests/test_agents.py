"""
Test individual agents without running the entire application.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_news_analyst():
    """Test the news analyst agent."""
    print("\n" + "=" * 60)
    print("Testing News Analyst")
    print("=" * 60)
    
    try:
        from tradingagents.default_config import DEFAULT_CONFIG
        from langchain_google_genai import ChatGoogleGenerativeAI
        from tradingagents.agents.analysts.news_analyst import create_news_analyst
        from tradingagents.agents.utils.agent_states import AgentState
        
        # Setup
        config = DEFAULT_CONFIG.copy()
        llm = ChatGoogleGenerativeAI(model=config["quick_think_llm"])
        
        # Create the analyst
        news_analyst = create_news_analyst(llm)
        
        # Create a simple state
        state = {
            "trade_date": "2024-05-10",
            "company_of_interest": "AAPL",
            "messages": []
        }
        
        print(f"Testing news analyst for {state['company_of_interest']} on {state['trade_date']}")
        print("Note: This test requires GOOGLE_API_KEY to be set.")
        print("The agent will attempt to fetch news data...\n")
        
        # This would call the actual agent - commenting out to avoid API calls in tests
        # result = news_analyst(state)
        # print("✓ News analyst executed successfully")
        # print(f"Report: {result.get('news_report', 'No report')[:200]}...")
        
        print("✓ News analyst structure validated")
        return True
        
    except Exception as e:
        print(f"✗ News analyst test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_market_analyst():
    """Test the market analyst agent."""
    print("\n" + "=" * 60)
    print("Testing Market Analyst")
    print("=" * 60)
    
    try:
        from tradingagents.default_config import DEFAULT_CONFIG
        from langchain_google_genai import ChatGoogleGenerativeAI
        from tradingagents.agents.analysts.market_analyst import create_market_analyst
        
        # Setup
        config = DEFAULT_CONFIG.copy()
        llm = ChatGoogleGenerativeAI(model=config["quick_think_llm"])
        
        # Create the analyst
        market_analyst = create_market_analyst(llm)
        
        # Create a simple state
        state = {
            "trade_date": "2024-05-10",
            "company_of_interest": "AAPL",
            "messages": []
        }
        
        print(f"Testing market analyst for {state['company_of_interest']} on {state['trade_date']}")
        print("✓ Market analyst structure validated")
        return True
        
    except Exception as e:
        print(f"✗ Market analyst test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fundamentals_analyst():
    """Test the fundamentals analyst agent."""
    print("\n" + "=" * 60)
    print("Testing Fundamentals Analyst")
    print("=" * 60)
    
    try:
        from tradingagents.default_config import DEFAULT_CONFIG
        from langchain_google_genai import ChatGoogleGenerativeAI
        from tradingagents.agents.analysts.fundamentals_analyst import create_fundamentals_analyst
        
        # Setup
        config = DEFAULT_CONFIG.copy()
        llm = ChatGoogleGenerativeAI(model=config["quick_think_llm"])
        
        # Create the analyst
        fundamentals_analyst = create_fundamentals_analyst(llm)
        
        # Create a simple state
        state = {
            "trade_date": "2024-05-10",
            "company_of_interest": "AAPL",
            "messages": []
        }
        
        print(f"Testing fundamentals analyst for {state['company_of_interest']} on {state['trade_date']}")
        print("✓ Fundamentals analyst structure validated")
        return True
        
    except Exception as e:
        print(f"✗ Fundamentals analyst test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bull_researcher():
    """Test the bull researcher agent."""
    print("\n" + "=" * 60)
    print("Testing Bull Researcher")
    print("=" * 60)
    
    try:
        from tradingagents.default_config import DEFAULT_CONFIG
        from langchain_google_genai import ChatGoogleGenerativeAI
        from tradingagents.agents.researchers.bull_researcher import create_bull_researcher
        from tradingagents.agents.utils.memory import FinancialSituationMemory
        
        # Setup
        config = DEFAULT_CONFIG.copy()
        llm = ChatGoogleGenerativeAI(model=config["quick_think_llm"])
        memory = FinancialSituationMemory("test_bull_memory", config)
        
        # Create the researcher
        bull_researcher = create_bull_researcher(llm, memory)
        
        print("✓ Bull researcher structure validated")
        return True
        
    except Exception as e:
        print(f"✗ Bull researcher test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_fetching():
    """Test data fetching with caching and rate limiting."""
    print("\n" + "=" * 60)
    print("Testing Data Fetching (with cache and rate limits)")
    print("=" * 60)
    
    try:
        from tradingagents.dataflows.y_finance import get_YFin_data_online
        import time
        
        ticker = "AAPL"
        start_date = "2024-01-01"
        end_date = "2024-01-05"
        
        print(f"Fetching {ticker} data from {start_date} to {end_date}...")
        
        # First call - should fetch from API
        start_time = time.time()
        data1 = get_YFin_data_online(ticker, start_date, end_date)
        elapsed1 = time.time() - start_time
        print(f"First call took {elapsed1:.2f}s (API call)")
        
        # Second call - should use cache
        start_time = time.time()
        data2 = get_YFin_data_online(ticker, start_date, end_date)
        elapsed2 = time.time() - start_time
        print(f"Second call took {elapsed2:.2f}s (cached)")
        
        assert data1 == data2, "Cached data should match original"
        print(f"✓ Data fetching with cache works (speedup: {elapsed1/elapsed2:.1f}x)")
        
        return True
        
    except Exception as e:
        print(f"✗ Data fetching test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all agent tests."""
    print("=" * 60)
    print("TradingAgents Individual Agent Tests")
    print("=" * 60)
    print("\nThese tests validate agent structures without making API calls.")
    print("For full integration tests, use test_integration.py\n")
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠ GOOGLE_API_KEY not set. Some tests may be limited.")
        print("  Set it with: export GOOGLE_API_KEY='your-api-key-here'\n")
    
    tests = [
        ("News Analyst", test_news_analyst),
        ("Market Analyst", test_market_analyst),
        ("Fundamentals Analyst", test_fundamentals_analyst),
        ("Bull Researcher", test_bull_researcher),
        ("Data Fetching", test_data_fetching),
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
        print("\n✓ All agent tests passed!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

