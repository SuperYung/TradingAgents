#!/usr/bin/env python3
"""
Debug script to test Yahoo Finance API response directly.
Run this with: python3 debug_yfinance_raw.py
"""
import sys
import json
from datetime import datetime

try:
    import yfinance as yf
except ImportError:
    print("ERROR: yfinance not installed")
    print("Install with: pip install yfinance")
    sys.exit(1)

print("=" * 80)
print("YAHOO FINANCE NEWS DEBUG - AAPL")
print("=" * 80)
print(f"Current system date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Get ticker
ticker = yf.Ticker('AAPL')
news = ticker.news

print(f"📰 Number of articles returned by Yahoo Finance: {len(news) if news else 0}")
print()

if not news or len(news) == 0:
    print("❌ Yahoo Finance returned NO news articles!")
    print()
    print("Possible causes:")
    print("  1. Yahoo Finance API is down")
    print("  2. Network connectivity issues")
    print("  3. Rate limiting")
    sys.exit(1)

print("✅ Yahoo Finance returned news articles")
print()
print("=" * 80)
print("ANALYZING FIRST 5 ARTICLES")
print("=" * 80)

valid_count = 0
invalid_count = 0

for i, article in enumerate(news[:5], 1):
    print(f"\n📄 Article #{i}")
    print("-" * 80)
    
    # Extract fields
    title = article.get('title', '')
    publisher = article.get('publisher', '')
    timestamp = article.get('providerPublishTime', 0)
    link = article.get('link', '')
    
    # Display raw data
    print(f"  Title (raw):      {repr(title)}")
    print(f"  Publisher (raw):  {repr(publisher)}")
    print(f"  Timestamp (raw):  {timestamp}")
    print(f"  Link:             {link[:80] if link else 'N/A'}")
    
    # Validation checks
    print()
    print("  🔍 Validation:")
    
    title_valid = bool(title and title.strip() and title != 'No title')
    timestamp_valid = bool(timestamp and timestamp > 0)
    
    print(f"    Title valid:     {title_valid} {'' if title_valid else '← INVALID'}")
    print(f"    Timestamp valid: {timestamp_valid} {'' if timestamp_valid else '← INVALID (0 or missing)'}")
    
    if title_valid and timestamp_valid:
        try:
            pub_date = datetime.fromtimestamp(timestamp)
            print(f"    Published date:  {pub_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    ✅ VALID ARTICLE")
            valid_count += 1
        except Exception as e:
            print(f"    ❌ Error converting timestamp: {e}")
            invalid_count += 1
    else:
        print(f"    ❌ INVALID ARTICLE - Will be filtered out")
        invalid_count += 1

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total articles returned:  {len(news)}")
print(f"Valid articles (first 5): {valid_count}")
print(f"Invalid articles:         {invalid_count}")
print()

if valid_count == 0:
    print("❌ ALL ARTICLES ARE INVALID!")
    print()
    print("This explains why your agent cannot retrieve news.")
    print()
    print("Root causes:")
    print("  1. Yahoo Finance API data quality issues")
    print("  2. API returning placeholder/empty data")
    print("  3. Cached bad response (if cache is enabled)")
    print()
    print("Next steps:")
    print("  1. Check if cache directory exists: tradingagents/dataflows/cache/")
    print("  2. Delete cache if it exists")
    print("  3. Try different ticker (e.g., MSFT, TSLA)")
    print("  4. Consider using Google News as alternative")
else:
    print("✅ Some valid articles found")
    print()
    print("If your agent still shows no news, check:")
    print("  1. Cache directory: tradingagents/dataflows/cache/")
    print("  2. Make sure cache is not serving stale data")

print()
print("Full first article data:")
print("-" * 80)
if news:
    print(json.dumps(news[0], indent=2, default=str))

