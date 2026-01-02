#!/usr/bin/env python3
"""
Test the fixed Yahoo Finance news functions.
"""
import sys
sys.path.insert(0, '.')

from tradingagents.dataflows.y_finance import get_yfinance_news, get_yfinance_global_news

print("=" * 80)
print("TESTING FIXED YAHOO FINANCE NEWS FUNCTIONS")
print("=" * 80)
print()

# Test 1: Ticker-specific news
print("Test 1: Getting news for AAPL")
print("-" * 80)
result = get_yfinance_news("AAPL", "2025-12-24", "2025-12-31")
print(result)
print()

# Test 2: Global news
print("=" * 80)
print("Test 2: Getting global market news")
print("-" * 80)
result = get_yfinance_global_news("2025-12-31", look_back_days=7, limit=5)
print(result)
print()

print("=" * 80)
print("✅ Tests complete!")
print("If you see real news articles above, the fix worked!")
print("=" * 80)

