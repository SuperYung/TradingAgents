"""
Data Source Manager - Orchestrates multiple data providers with automatic fallback.
"""

import os
from typing import Optional, Dict, Any, List
import asyncio
from pathlib import Path

try:
    import toml
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False

from .providers.base_provider import BaseStockDataProvider, ProviderError, RateLimitError
from .providers.us import YahooFinanceProvider, GoogleProvider, AlphaVantageProvider
from tradingagents.utils.logging_manager import get_logger

logger = get_logger("tradingagents.dataflows.data_source_manager")


class DataSourceManager:
    """
    Manages multiple data providers with automatic fallback.
    
    Features:
    - Priority-based provider selection
    - Automatic fallback on failure
    - Centralized configuration
    - Provider health monitoring
    - Unified interface for all data operations
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Data Source Manager.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config = self._load_config(config_path)
        self.providers: List[BaseStockDataProvider] = []
        self._initialize_providers()
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from TOML file or use defaults."""
        if config_path and TOML_AVAILABLE:
            try:
                with open(config_path, 'r') as f:
                    config = toml.load(f)
                logger.info(f"Loaded configuration from {config_path}")
                return config
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        # Try default config path
        default_path = Path("config/data_sources.toml")
        if default_path.exists() and TOML_AVAILABLE:
            try:
                with open(default_path, 'r') as f:
                    config = toml.load(f)
                logger.info(f"Loaded configuration from {default_path}")
                return config
            except Exception as e:
                logger.warning(f"Failed to load default config: {e}")
        
        # Use default configuration
        logger.info("Using default configuration")
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'providers': {
                'alphavantage': {
                    'enabled': bool(os.getenv('ALPHA_VANTAGE_API_KEY')),
                    'priority': 1,
                    'cache_ttl': 3600
                },
                'yfinance': {
                    'enabled': True,
                    'priority': 2,
                    'cache_ttl': 3600
                },
                'google': {
                    'enabled': True,
                    'priority': 3,
                    'cache_ttl': 3600
                }
            }
        }
    
    def _initialize_providers(self):
        """Initialize all configured providers."""
        provider_classes = {
            'alphavantage': AlphaVantageProvider,
            'yfinance': YahooFinanceProvider,
            'google': GoogleProvider
        }
        
        for provider_name, provider_class in provider_classes.items():
            provider_config = self.config.get('providers', {}).get(provider_name, {})
            
            if not provider_config.get('enabled', True):
                logger.info(f"Provider {provider_name} is disabled")
                continue
            
            try:
                # Initialize provider with configuration
                cache_ttl = provider_config.get('cache_ttl', 3600)
                provider = provider_class(cache_ttl=cache_ttl)
                
                if provider.is_available():
                    self.providers.append(provider)
                    logger.info(f"✅ Initialized provider: {provider.name} (priority={provider.priority})")
                else:
                    logger.warning(f"⚠️  Provider {provider_name} not available")
                    
            except Exception as e:
                logger.error(f"❌ Failed to initialize provider {provider_name}: {e}")
        
        # Sort providers by priority (lower = higher priority)
        self.providers.sort(key=lambda p: p.priority)
        
        if not self.providers:
            logger.error("❌ No providers available!")
        else:
            logger.info(f"Initialized {len(self.providers)} provider(s): " + 
                       ", ".join(p.name for p in self.providers))
    
    async def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get stock quote with automatic fallback.
        
        Args:
            symbol: Stock ticker symbol
        
        Returns:
            Quote data dict or None if all providers fail
        """
        logger.debug(f"Fetching quote for {symbol}")
        
        for provider in self.providers:
            try:
                logger.debug(f"Trying provider: {provider.name}")
                data = await provider.get_stock_quote(symbol)
                
                if data:
                    logger.info(f"✅ Got quote for {symbol} from {provider.name}")
                    return data
                else:
                    logger.warning(f"⚠️  No data from {provider.name}")
                    
            except RateLimitError as e:
                logger.warning(f"⚠️  Rate limit on {provider.name}: {e}")
                continue
            except ProviderError as e:
                logger.warning(f"⚠️  {provider.name} error: {e}")
                continue
            except Exception as e:
                logger.error(f"❌ Unexpected error with {provider.name}: {e}")
                continue
        
        logger.error(f"❌ All providers failed for quote: {symbol}")
        return None
    
    async def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = 'daily'
    ) -> Optional[str]:
        """
        Get historical data with automatic fallback.
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Data interval
        
        Returns:
            CSV data string or None if all providers fail
        """
        logger.debug(f"Fetching historical data for {symbol}")
        
        for provider in self.providers:
            try:
                logger.debug(f"Trying provider: {provider.name}")
                data = await provider.get_historical_data(symbol, start_date, end_date, interval)
                
                if data:
                    logger.info(f"✅ Got historical data for {symbol} from {provider.name}")
                    return data
                else:
                    logger.warning(f"⚠️  No data from {provider.name}")
                    
            except RateLimitError as e:
                logger.warning(f"⚠️  Rate limit on {provider.name}: {e}")
                continue
            except ProviderError as e:
                logger.warning(f"⚠️  {provider.name} error: {e}")
                continue
            except Exception as e:
                logger.error(f"❌ Unexpected error with {provider.name}: {e}")
                continue
        
        logger.error(f"❌ All providers failed for historical data: {symbol}")
        return None
    
    async def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get stock/company information with automatic fallback."""
        logger.debug(f"Fetching stock info for {symbol}")
        
        for provider in self.providers:
            try:
                logger.debug(f"Trying provider: {provider.name}")
                data = await provider.get_stock_info(symbol)
                
                if data:
                    logger.info(f"✅ Got stock info for {symbol} from {provider.name}")
                    return data
                else:
                    logger.warning(f"⚠️  No data from {provider.name}")
                    
            except RateLimitError as e:
                logger.warning(f"⚠️  Rate limit on {provider.name}: {e}")
                continue
            except ProviderError as e:
                logger.warning(f"⚠️  {provider.name} error: {e}")
                continue
            except Exception as e:
                logger.error(f"❌ Unexpected error with {provider.name}: {e}")
                continue
        
        logger.error(f"❌ All providers failed for stock info: {symbol}")
        return None
    
    async def get_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get fundamental data with automatic fallback."""
        logger.debug(f"Fetching fundamentals for {symbol}")
        
        for provider in self.providers:
            try:
                logger.debug(f"Trying provider: {provider.name}")
                data = await provider.get_fundamentals(symbol)
                
                if data:
                    logger.info(f"✅ Got fundamentals for {symbol} from {provider.name}")
                    return data
                else:
                    logger.warning(f"⚠️  No data from {provider.name}")
                    
            except RateLimitError as e:
                logger.warning(f"⚠️  Rate limit on {provider.name}: {e}")
                continue
            except ProviderError as e:
                logger.warning(f"⚠️  {provider.name} error: {e}")
                continue
            except Exception as e:
                logger.error(f"❌ Unexpected error with {provider.name}: {e}")
                continue
        
        logger.error(f"❌ All providers failed for fundamentals: {symbol}")
        return None
    
    async def get_news(
        self,
        symbol: Optional[str] = None,
        limit: int = 10
    ) -> Optional[List[Dict[str, Any]]]:
        """Get news with automatic fallback."""
        logger.debug(f"Fetching news for {symbol or 'market'}")
        
        for provider in self.providers:
            try:
                logger.debug(f"Trying provider: {provider.name}")
                data = await provider.get_news(symbol, limit)
                
                if data:
                    logger.info(f"✅ Got {len(data)} news articles from {provider.name}")
                    return data
                else:
                    logger.warning(f"⚠️  No news from {provider.name}")
                    
            except RateLimitError as e:
                logger.warning(f"⚠️  Rate limit on {provider.name}: {e}")
                continue
            except ProviderError as e:
                logger.warning(f"⚠️  {provider.name} error: {e}")
                continue
            except Exception as e:
                logger.error(f"❌ Unexpected error with {provider.name}: {e}")
                continue
        
        logger.error(f"❌ All providers failed for news")
        return None
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers."""
        status = {}
        for provider in self.providers:
            status[provider.name] = {
                'available': provider.is_available(),
                'priority': provider.priority,
                'class': provider.__class__.__name__
            }
        return status
    
    def __repr__(self) -> str:
        """String representation."""
        provider_names = [p.name for p in self.providers]
        return f"<DataSourceManager(providers={provider_names})>"


# Global instance for easy access
_data_source_manager: Optional[DataSourceManager] = None


def get_data_source_manager(config_path: Optional[str] = None) -> DataSourceManager:
    """
    Get global DataSourceManager instance.
    
    Args:
        config_path: Optional configuration file path
    
    Returns:
        DataSourceManager instance
    """
    global _data_source_manager
    if _data_source_manager is None:
        _data_source_manager = DataSourceManager(config_path)
    return _data_source_manager


def reset_data_source_manager():
    """Reset the global DataSourceManager instance."""
    global _data_source_manager
    _data_source_manager = None

