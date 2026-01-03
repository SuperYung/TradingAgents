"""
Base provider interface for stock data sources.
Defines the contract that all data providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
from functools import wraps


def async_to_sync(func):
    """Decorator to run async functions synchronously if needed."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if asyncio.iscoroutinefunction(func):
            return loop.run_until_complete(func(*args, **kwargs))
        return func(*args, **kwargs)
    return wrapper


class BaseStockDataProvider(ABC):
    """
    Base class for stock data providers.
    
    All data providers must implement this interface to ensure
    compatibility with the DataSourceManager fallback system.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Provider name for logging and identification.
        
        Returns:
            str: Unique provider name (e.g., 'yahoo_finance', 'alpha_vantage')
        """
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """
        Priority for provider selection (lower = higher priority).
        
        The DataSourceManager will try providers in priority order:
        - 1: Primary (fastest, most reliable)
        - 2: Secondary (backup)
        - 3: Tertiary (last resort)
        
        Returns:
            int: Priority level (1-10)
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if provider is available and configured.
        
        Returns:
            bool: True if provider can be used, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get real-time or latest stock quote.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        
        Returns:
            Dict with keys:
                - symbol: Stock symbol
                - price: Current/latest price
                - change: Price change
                - change_percent: Percentage change
                - volume: Trading volume
                - timestamp: Quote timestamp
            None if data unavailable
        """
        pass
    
    @abstractmethod
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str,
        interval: str = 'daily'
    ) -> Optional[str]:
        """
        Get historical OHLCV data.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval ('daily', 'weekly', 'monthly')
        
        Returns:
            CSV-formatted string with columns:
                Date, Open, High, Low, Close, Volume
            None if data unavailable
        """
        pass
    
    @abstractmethod
    async def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get company/stock information.
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            Dict with keys:
                - symbol: Stock symbol
                - name: Company name
                - sector: Business sector
                - industry: Industry classification
                - market_cap: Market capitalization
                - description: Company description
                - website: Company website
            None if data unavailable
        """
        pass
    
    @abstractmethod
    async def get_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get fundamental data (financials, ratios).
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            Dict with keys:
                - pe_ratio: Price to earnings ratio
                - eps: Earnings per share
                - dividend_yield: Dividend yield
                - beta: Stock beta
                - 52_week_high: 52-week high
                - 52_week_low: 52-week low
            None if data unavailable
        """
        pass
    
    async def get_news(
        self, 
        symbol: Optional[str] = None, 
        limit: int = 10
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get news articles (optional, not all providers support this).
        
        Args:
            symbol: Stock ticker symbol (None for general market news)
            limit: Maximum number of articles
        
        Returns:
            List of dicts with keys:
                - title: Article title
                - summary: Article summary
                - url: Article URL
                - published: Publication timestamp
                - source: News source
            None if not supported or unavailable
        """
        return None
    
    async def get_technical_indicators(
        self,
        symbol: str,
        indicator: str,
        **params
    ) -> Optional[Dict[str, Any]]:
        """
        Get technical indicators (optional).
        
        Args:
            symbol: Stock ticker symbol
            indicator: Indicator name (e.g., 'SMA', 'RSI', 'MACD')
            **params: Indicator-specific parameters
        
        Returns:
            Dict with indicator data
            None if not supported or unavailable
        """
        return None
    
    def __repr__(self) -> str:
        """String representation of provider."""
        return f"<{self.__class__.__name__}(priority={self.priority}, available={self.is_available()})>"


class ProviderError(Exception):
    """Base exception for provider errors."""
    pass


class RateLimitError(ProviderError):
    """Raised when provider rate limit is exceeded."""
    pass


class AuthenticationError(ProviderError):
    """Raised when API authentication fails."""
    pass


class DataNotFoundError(ProviderError):
    """Raised when requested data is not found."""
    pass

