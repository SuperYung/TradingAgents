"""
Yahoo Finance Data Provider
Priority: 1 (Primary source - free, reliable, no API key required)
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import asyncio
from functools import lru_cache
import time

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

from ..base_provider import (
    BaseStockDataProvider,
    ProviderError,
    RateLimitError,
    DataNotFoundError
)
from tradingagents.utils.logging_manager import get_logger

logger = get_logger("tradingagents.dataflows.providers.yfinance")


class YahooFinanceProvider(BaseStockDataProvider):
    """
    Yahoo Finance data provider.
    
    Features:
    - Free, no API key required
    - Real-time quotes (15-20 minute delay)
    - Historical data
    - Company information
    - News articles
    - Caching with 1-hour TTL
    - Rate limiting protection
    """
    
    def __init__(self, cache_ttl: int = 3600):
        """
        Initialize Yahoo Finance provider.
        
        Args:
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._rate_limit_delay = 0.1  # 100ms between requests
        self._last_request_time = 0
    
    @property
    def name(self) -> str:
        return "yahoo_finance"
    
    @property
    def priority(self) -> int:
        return 1  # Highest priority
    
    def is_available(self) -> bool:
        """Check if yfinance library is available."""
        if not YFINANCE_AVAILABLE:
            logger.warning("yfinance library not installed")
            return False
        return True
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache if not expired."""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for {key}")
                return data
            else:
                # Cache expired
                del self._cache[key]
        return None
    
    def _add_to_cache(self, key: str, data: Any):
        """Add data to cache with timestamp."""
        self._cache[key] = (data, time.time())
        logger.debug(f"Cached {key}")
    
    async def _rate_limit(self):
        """Apply rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._rate_limit_delay:
            await asyncio.sleep(self._rate_limit_delay - elapsed)
        self._last_request_time = time.time()
    
    async def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time stock quote from Yahoo Finance."""
        try:
            # Check cache first
            cache_key = f"quote_{symbol}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Apply rate limiting
            await self._rate_limit()
            
            logger.debug(f"Fetching quote for {symbol} from Yahoo Finance")
            
            # Fetch data
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or 'currentPrice' not in info:
                logger.warning(f"No quote data available for {symbol}")
                return None
            
            quote_data = {
                'symbol': symbol.upper(),
                'price': info.get('currentPrice') or info.get('regularMarketPrice'),
                'change': info.get('regularMarketChange'),
                'change_percent': info.get('regularMarketChangePercent'),
                'volume': info.get('regularMarketVolume'),
                'timestamp': datetime.now().isoformat(),
                'provider': self.name
            }
            
            # Cache the result
            self._add_to_cache(cache_key, quote_data)
            
            logger.info(f"✅ Retrieved quote for {symbol}: ${quote_data['price']}")
            return quote_data
            
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            raise ProviderError(f"Yahoo Finance quote error: {e}")
    
    async def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = 'daily'
    ) -> Optional[str]:
        """Get historical OHLCV data."""
        try:
            # Check cache
            cache_key = f"historical_{symbol}_{start_date}_{end_date}_{interval}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Apply rate limiting
            await self._rate_limit()
            
            logger.debug(f"Fetching historical data for {symbol}")
            
            # Map interval
            interval_map = {
                'daily': '1d',
                'weekly': '1wk',
                'monthly': '1mo'
            }
            yf_interval = interval_map.get(interval, '1d')
            
            # Fetch data
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval=yf_interval)
            
            if df.empty:
                logger.warning(f"No historical data for {symbol}")
                return None
            
            # Convert to CSV string
            csv_data = df.to_csv()
            
            # Cache the result
            self._add_to_cache(cache_key, csv_data)
            
            logger.info(f"✅ Retrieved {len(df)} historical records for {symbol}")
            return csv_data
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            raise ProviderError(f"Yahoo Finance historical data error: {e}")
    
    async def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get company information."""
        try:
            # Check cache
            cache_key = f"info_{symbol}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Apply rate limiting
            await self._rate_limit()
            
            logger.debug(f"Fetching info for {symbol}")
            
            # Fetch data
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                logger.warning(f"No info available for {symbol}")
                return None
            
            stock_info = {
                'symbol': symbol.upper(),
                'name': info.get('longName') or info.get('shortName'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'market_cap': info.get('marketCap'),
                'description': info.get('longBusinessSummary'),
                'website': info.get('website'),
                'employees': info.get('fullTimeEmployees'),
                'country': info.get('country'),
                'city': info.get('city'),
                'provider': self.name
            }
            
            # Cache the result
            self._add_to_cache(cache_key, stock_info)
            
            logger.info(f"✅ Retrieved info for {symbol}: {stock_info['name']}")
            return stock_info
            
        except Exception as e:
            logger.error(f"Error fetching info for {symbol}: {e}")
            raise ProviderError(f"Yahoo Finance info error: {e}")
    
    async def get_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get fundamental data."""
        try:
            # Check cache
            cache_key = f"fundamentals_{symbol}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Apply rate limiting
            await self._rate_limit()
            
            logger.debug(f"Fetching fundamentals for {symbol}")
            
            # Fetch data
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info:
                return None
            
            fundamentals = {
                'symbol': symbol.upper(),
                'pe_ratio': info.get('trailingPE') or info.get('forwardPE'),
                'eps': info.get('trailingEps'),
                'dividend_yield': info.get('dividendYield'),
                'beta': info.get('beta'),
                '52_week_high': info.get('fiftyTwoWeekHigh'),
                '52_week_low': info.get('fiftyTwoWeekLow'),
                'price_to_book': info.get('priceToBook'),
                'profit_margin': info.get('profitMargins'),
                'revenue': info.get('totalRevenue'),
                'earnings_growth': info.get('earningsQuarterlyGrowth'),
                'provider': self.name
            }
            
            # Cache the result
            self._add_to_cache(cache_key, fundamentals)
            
            logger.info(f"✅ Retrieved fundamentals for {symbol}")
            return fundamentals
            
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {symbol}: {e}")
            raise ProviderError(f"Yahoo Finance fundamentals error: {e}")
    
    async def get_news(
        self,
        symbol: Optional[str] = None,
        limit: int = 10
    ) -> Optional[List[Dict[str, Any]]]:
        """Get news articles."""
        try:
            if not symbol:
                logger.warning("Yahoo Finance requires symbol for news")
                return None
            
            # Check cache
            cache_key = f"news_{symbol}_{limit}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Apply rate limiting
            await self._rate_limit()
            
            logger.debug(f"Fetching news for {symbol}")
            
            # Fetch data
            ticker = yf.Ticker(symbol)
            news_data = ticker.news
            
            if not news_data:
                return None
            
            articles = []
            for item in news_data[:limit]:
                articles.append({
                    'title': item.get('title'),
                    'summary': item.get('summary'),
                    'url': item.get('link'),
                    'published': datetime.fromtimestamp(item.get('providerPublishTime', 0)).isoformat(),
                    'source': item.get('publisher'),
                    'provider': self.name
                })
            
            # Cache the result
            self._add_to_cache(cache_key, articles)
            
            logger.info(f"✅ Retrieved {len(articles)} news articles for {symbol}")
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return None

