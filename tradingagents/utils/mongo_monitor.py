#!/usr/bin/env python3
"""
MongoDB Monitor
CLI utility to inspect and manage MongoDB storage
"""

import argparse
import sys
from datetime import datetime, timedelta
from tradingagents.config.mongodb_manager import get_mongodb_manager
from tradingagents.dataflows.mongodb import (
    AnalysisRepository,
    HistoricalRepository,
    NewsRepository,
    UsageRepository
)


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_health():
    """Check MongoDB health and connection status"""
    print_header("MongoDB Health Check")
    
    manager = get_mongodb_manager()
    
    if not manager.is_available():
        print("❌ MongoDB: NOT AVAILABLE")
        print("   Reason: Connection failed or disabled")
        print(f"   Enabled: {manager.enabled}")
        print(f"   Host: {manager.host}:{manager.port}")
        return False
    
    # Test connection
    healthy = manager.health_check()
    
    if healthy:
        print("✅ MongoDB: CONNECTED AND HEALTHY")
        print(f"   📊 Database: {manager.database}")
        print(f"   🔗 Host: {manager.host}:{manager.port}")
        print(f"   🏊 Pool: {manager.min_pool_size}-{manager.max_pool_size} connections")
        print(f"   ⏱️  Timeouts: connect={manager.connect_timeout}ms, socket={manager.socket_timeout}ms")
    else:
        print("⚠️  MongoDB: CONNECTION DEGRADED")
        print("   Health check failed - connection may be unstable")
    
    return healthy


def show_stats():
    """Show statistics from all repositories"""
    print_header("MongoDB Statistics")
    
    manager = get_mongodb_manager()
    if not manager.is_available():
        print("❌ MongoDB not available")
        return
    
    # Analysis Repository
    print("\n📊 Analysis Reports:")
    analysis_repo = AnalysisRepository()
    stats = analysis_repo.get_stats()
    if stats.get('available'):
        print(f"   Total Analyses: {stats['total_analyses']}")
        if stats.get('by_status'):
            print(f"   By Status: {stats['by_status']}")
        if stats.get('by_action'):
            print(f"   By Action: {stats['by_action']}")
    else:
        print("   ⚠️  Not available")
    
    # Historical Repository
    print("\n📈 Historical Prices:")
    hist_repo = HistoricalRepository()
    stats = hist_repo.get_stats()
    if stats.get('available'):
        print(f"   Total Records: {stats['total_records']}")
        print(f"   Unique Symbols: {stats['unique_symbols']}")
        if stats.get('symbols_sample'):
            print(f"   Sample Symbols: {', '.join(stats['symbols_sample'][:5])}")
    else:
        print("   ⚠️  Not available")
    
    # News Repository
    print("\n📰 News Articles:")
    news_repo = NewsRepository()
    stats = news_repo.get_stats()
    if stats.get('available'):
        print(f"   Total Articles: {stats['total_articles']}")
        print(f"   Unique Symbols: {stats['unique_symbols']}")
        print(f"   Recent (7 days): {stats['recent_7days']}")
    else:
        print("   ⚠️  Not available")
    
    # Usage Repository
    print("\n💰 Token Usage:")
    usage_repo = UsageRepository()
    stats = usage_repo.get_stats()
    if stats.get('available'):
        print(f"   Total Records: {stats['total_records']}")
        print(f"   Unique Providers: {stats['unique_providers']}")
        print(f"   Providers: {', '.join(stats.get('providers', []))}")
    else:
        print("   ⚠️  Not available")


def show_recent_analyses(limit: int = 10):
    """Show recent analyses"""
    print_header(f"Recent Analyses (Last {limit})")
    
    analysis_repo = AnalysisRepository()
    if not analysis_repo.collection:
        print("❌ Analysis repository not available")
        return
    
    analyses = analysis_repo.get_recent_analyses(limit)
    
    if not analyses:
        print("   No analyses found")
        return
    
    for i, analysis in enumerate(analyses, 1):
        print(f"\n{i}. {analysis.get('symbol')} - {analysis.get('analysis_date')}")
        print(f"   ID: {analysis.get('analysis_id')}")
        print(f"   Recommendation: {analysis.get('recommendation', 'N/A')}")
        print(f"   Status: {analysis.get('status', 'N/A')}")
        if analysis.get('decision'):
            print(f"   Action: {analysis['decision'].get('action', 'N/A')}")


def show_usage_summary(days: int = 7):
    """Show token usage summary"""
    print_header(f"Token Usage Summary (Last {days} Days)")
    
    usage_repo = UsageRepository()
    if not usage_repo.collection:
        print("❌ Usage repository not available")
        return
    
    summary = usage_repo.get_usage_summary(days)
    
    if not summary.get('available'):
        print("❌ Usage data not available")
        return
    
    print(f"\n📊 Overall:")
    print(f"   Total Records: {summary['total_records']}")
    print(f"   Total Tokens: {summary['total_tokens']:,}")
    print(f"   Total Cost: ${summary['total_cost']:.2f}")
    
    if summary.get('by_provider'):
        print(f"\n💳 By Provider:")
        for provider, data in summary['by_provider'].items():
            print(f"   {provider}:")
            print(f"     Calls: {data['count']}")
            print(f"     Tokens: {data['tokens']:,}")
            print(f"     Cost: ${data['cost']:.2f}")
    
    if summary.get('by_model'):
        print(f"\n🤖 By Model:")
        for model, data in summary['by_model'].items():
            print(f"   {model}:")
            print(f"     Calls: {data['count']}")
            print(f"     Tokens: {data['tokens']:,}")
            print(f"     Cost: ${data['cost']:.2f}")


def clean_old_data(days: int, data_type: str = 'all'):
    """Clean old data from MongoDB"""
    print_header(f"Cleaning Data Older Than {days} Days")
    
    manager = get_mongodb_manager()
    if not manager.is_available():
        print("❌ MongoDB not available")
        return
    
    deleted_count = 0
    
    if data_type in ['all', 'historical']:
        print("\n🗑️  Cleaning historical data...")
        hist_repo = HistoricalRepository()
        count = hist_repo.delete_old_data(days)
        print(f"   Deleted {count} records")
        deleted_count += count
    
    if data_type in ['all', 'news']:
        print("\n🗑️  Cleaning news articles...")
        news_repo = NewsRepository()
        count = news_repo.delete_old_news(days)
        print(f"   Deleted {count} articles")
        deleted_count += count
    
    if data_type in ['all', 'usage']:
        print("\n🗑️  Cleaning usage records...")
        usage_repo = UsageRepository()
        count = usage_repo.delete_old_usage(days)
        print(f"   Deleted {count} records")
        deleted_count += count
    
    print(f"\n✅ Total deleted: {deleted_count} records")


def main():
    parser = argparse.ArgumentParser(
        description="MongoDB monitoring and management utility for TradingAgents"
    )
    
    parser.add_argument(
        '--health',
        action='store_true',
        help='Check MongoDB connection health'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics from all collections'
    )
    
    parser.add_argument(
        '--recent',
        type=int,
        metavar='N',
        help='Show N most recent analyses'
    )
    
    parser.add_argument(
        '--usage',
        type=int,
        metavar='DAYS',
        help='Show token usage summary for last N days'
    )
    
    parser.add_argument(
        '--clean',
        type=int,
        metavar='DAYS',
        help='Delete data older than N days'
    )
    
    parser.add_argument(
        '--type',
        choices=['all', 'historical', 'news', 'usage'],
        default='all',
        help='Data type for cleanup (default: all)'
    )
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    
    # Execute commands
    if args.health:
        check_health()
    
    if args.stats:
        show_stats()
    
    if args.recent:
        show_recent_analyses(args.recent)
    
    if args.usage:
        show_usage_summary(args.usage)
    
    if args.clean:
        # Confirm deletion
        response = input(f"\n⚠️  Delete data older than {args.clean} days? (yes/no): ")
        if response.lower() == 'yes':
            clean_old_data(args.clean, args.type)
        else:
            print("❌ Cancelled")
    
    print()  # Final newline


if __name__ == '__main__':
    main()

