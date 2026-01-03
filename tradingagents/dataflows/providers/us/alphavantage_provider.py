"""
Alpha Vantage Data Provider
Priority: 3 (Tertiary source - requires API key, rate limited)
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
import time

from ..base_provider import (
    BaseStockDataProvider,
    ProviderError,
    RateLimitError,
    AuthenticationError,
    DataNotFoundError
)
from tradingagents.utils.logging_manager import get_logger

logger = get_logger("tradingagents.dataflows.providers.alphavantage")


class AlphaVantageProvider(BaseStockDataProvider):
    """
    Alpha Vantage data provider.
    
    Features:
    - Comprehensive fundamental data
    - Technical indicators
    - News sentiment
    - Requires API key
    - Strict rate limiting (5 calls/minute for free tier)
    - Caching essential
    """
    
    def __init__(self, api_key: Optional[str] = None, cache_ttl: int = 3600):
        """
        Initialize Alpha Vantage provider.
        
        Args:
            api_key: Alpha Vantage API key (from env if not provided)
            cache_ttl: Cache time-to-live in seconds
        """
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._rate_limit_delay = 12.0  # 12 seconds between requests (5/min)
        self._last_request_time = 0
    
    @property
    def name(self) -> str:
        return "alpha_vantage"
    
    @property
    def priority(self) -> int:
        return 3  # Tertiary priority
    
    def is_available(self) -> bool:
        """Check if Alpha Vantage is available."""
        if not self.api_key:
            logger.warning("Alpha Vantage API key not configured")
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
                del self._cache[key]
        return None
    
    def _add_to_cache(self, key: str, data: Any):
        """Add data to cache."""
        self._cache[key] = (data, time.time())
    
    async def _rate_limit(self):
        """Apply strict rate limiting for Alpha Vantage."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._rate_limit_delay:
            wait_time = self._rate_limit_delay - elapsed
            logger.info(f"Rate limiting: waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
        self._last_request_time = time.time()
    
    async def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote from Alpha Vantage."""
        try:
            # Check cache first (important for rate limiting)
            cache_key = f"quote_{symbol}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Apply strict rate limiting
            await self._rate_limit()
            
            logger.debug(f"Fetching quote for {symbol} from Alpha Vantage")
            
            # Import existing Alpha Vantage functionality
            from tradingagents.dataflows.alpha_vantage import get_stock as _get_stock
            
            # Fetch data
            csv_data = _get_stock(symbol, outputsize='compact')
            
            if not csv_data or "Error" in csv_data:
                logger.warning(f"No quote data from Alpha Vantage for {symbol}")
                return None
            
            # Parse CSV to get latest quote
            lines = csv_data.strip().split('\n')
            if len(lines) < 2:
                return None
            
            headers = lines[0].split(',')
            latest = lines[1].split(',')
            
            quote_data = {
                'symbol': symbol.upper(),
                'price': float(latest[4]) if len(latest) > 4 else None,  # Close price
                'volume': int(latest[5]) if len(latest) > 5 else None,
                'timestamp': latest[0] if len(latest) > 0 else datetime.now().isoformat(),
                'provider': self.name
            }
            
            # Cache the result
            self._add_to_cache(cache_key, quote_data)
            
            logger.info(f"✅ Retrieved quote for {symbol} from Alpha Vantage")
            return quote_data
            
        except RateLimitError as e:
            logger.warning(f"Alpha Vantage rate limit: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage quote for {symbol}: {e}")
            raise ProviderError(f"Alpha Vantage error: {e}")
    
    async def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = 'daily'
    ) -> Optional[str]:
        """Get historical data from Alpha Vantage."""
        try:
            # Check cache
            cache_key = f"historical_{symbol}_{start_date}_{end_date}_{interval}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Apply rate limiting
            await self._rate_limit()
            
            logger.debug(f"Fetching historical data for {symbol} from Alpha Vantage")
            
            # Import existing functionality
            from tradingagents.dataflows.alpha_vantage import get_stock as _get_stock
            
            # Fetch data
            csv_data = _get_stock(symbol, outputsize='full')
            
            if not csv_data or "Error" in csv_data:
                return None
            
            # Filter by date range (Alpha Vantage returns all data)
            from tradingagents.dataflows.alpha_vantage_common import _filter_csv_by_date_range
            filtered_data = _filter_csv_by_date_range(csv_data, start_date, end_date)
            
            # Cache the result
            self._add_to_cache(cache_key, filtered_data)
            
            logger.info(f"✅ Retrieved historical data for {symbol} from Alpha Vantage")
            return filtered_data
            
        except RateLimitError as e:
            logger.warning(f"Alpha Vantage rate limit: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage historical data: {e}")
            raise ProviderError(f"Alpha Vantage error: {e}")
    
    async def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get company overview from Alpha Vantage."""
        try:
            # Check cache
            cache_key = f"info_{symbol}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Apply rate limiting
            await self._rate_limit()
            
            logger.debug(f"Fetching company info for {symbol} from Alpha Vantage")
            
            # Import existing functionality
            from tradingagents.dataflows.alpha_vantage import get_fundamentals as _get_fundamentals
            
            # Fetch data
            fundamentals_text = _get_fundamentals(symbol)
            
            if not fundamentals_text or "Error" in fundamentals_text:
                return None
            
            # Parse the fundamentals text (simplified)
            stock_info = {
                'symbol': symbol.upper(),
                'provider': self.name,
                'data': fundamentals_text  # Store as text for now
            }
            
            # Cache the result
            self._add_to_cache(cache_key, stock_info)
            
            logger.info(f"✅ Retrieved company info for {symbol} from Alpha Vantage")
            return stock_info
            
        except RateLimitError as e:
            logger.warning(f"Alpha Vantage rate limit: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage info: {e}")
            raise ProviderError(f"Alpha Vantage error: {e}")
    
    async def get_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get fundamental data from Alpha Vantage."""
        try:
            # Check cache
            cache_key = f"fundamentals_{symbol}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Apply rate limiting
            await self._rate_limit()
            
            logger.debug(f"Fetching fundamentals for {symbol} from Alpha Vantage")
            
            # Import existing functionality
            from tradingagents.dataflows.alpha_vantage import get_fundamentals as _get_fundamentals
            
            # Fetch data
            fundamentals_text = _get_fundamentals(symbol)
            
            if not fundamentals_text or "Error" in fundamentals_text:
                return None
            
            fundamentals = {
                'symbol': symbol.upper(),
                'provider': self.name,
                'data': fundamentals_text
            }
            
            # Cache the result
            self._add_to_cache(cache_key, fundamentals)
            
            logger.info(f"✅ Retrieved fundamentals for {symbol} from Alpha Vantage")
            return fundamentals
            
        except RateLimitError as e:
            logger.warning(f"Alpha Vantage rate limit: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage fundamentals: {e}")
            raise ProviderError(f"Alpha Vantage error: {e}")
    
    async def get_news(
        self,
        symbol: Optional[str] = None,
        limit: int = 10
    ) -> Optional[List[Dict[str, Any]]]:
        """Get news from Alpha Vantage."""
        try:
            # Check cache
            cache_key = f"news_{symbol}_{limit}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Apply rate limiting
            await self._rate_limit()
            
            logger.debug(f"Fetching news for {symbol} from Alpha Vantage")
            
            # Import existing functionality
            from tradingagents.dataflows.alpha_vantage import get_news as _get_news
            
            # Fetch data
            news_text = _get_news(symbol if symbol else "")
            
            if not news_text or "Error" in news_text:
                return None
            
            # Parse news text into structured format (simplified)
            articles = [{
                'title': 'Alpha Vantage News',
                'summary': news_text[:500],  # First 500 chars
                'provider': self.name
            }]
            
            # Cache the result
            self._add_to_cache(cache_key, articles)
            
            logger.info(f"✅ Retrieved news from Alpha Vantage")
            return articles
            
        except RateLimitError as e:
            logger.warning(f"Alpha Vantage rate limit: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage news: {e}")
            return None

