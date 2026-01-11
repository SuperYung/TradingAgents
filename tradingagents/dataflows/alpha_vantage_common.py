import os
import requests
import pandas as pd
import json
import hashlib
from datetime import datetime
from io import StringIO
from tradingagents.utils.logging_manager import get_logger
from tradingagents.dataflows.cache import get_cache
from tradingagents.dataflows.news_saver import get_news_saver

# Initialize logger
logger = get_logger("tradingagents.dataflows.alpha_vantage")

# Initialize cache and news saver
cache = get_cache()
news_saver = get_news_saver()

API_BASE_URL = "https://www.alphavantage.co/query"

def get_api_key() -> str:
    """Retrieve the API key for Alpha Vantage from environment variables."""
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        raise ValueError("ALPHA_VANTAGE_API_KEY environment variable is not set.")
    return api_key

def format_datetime_for_api(date_input) -> str:
    """Convert various date formats to YYYYMMDDTHHMM format required by Alpha Vantage API."""
    if isinstance(date_input, str):
        # If already in correct format, return as-is
        if len(date_input) == 13 and 'T' in date_input:
            return date_input
        # Try to parse common date formats
        try:
            dt = datetime.strptime(date_input, "%Y-%m-%d")
            return dt.strftime("%Y%m%dT0000")
        except ValueError:
            try:
                dt = datetime.strptime(date_input, "%Y-%m-%d %H:%M")
                return dt.strftime("%Y%m%dT%H%M")
            except ValueError:
                raise ValueError(f"Unsupported date format: {date_input}")
    elif isinstance(date_input, datetime):
        return date_input.strftime("%Y%m%dT%H%M")
    else:
        raise ValueError(f"Date must be string or datetime object, got {type(date_input)}")

class AlphaVantageRateLimitError(Exception):
    """Exception raised when Alpha Vantage API rate limit is exceeded."""
    pass

def _make_api_request(function_name: str, params: dict, use_cache: bool = True) -> dict | str:
    """Helper function to make API requests and handle responses with caching.
    
    Args:
        function_name: Alpha Vantage API function name
        params: API parameters
        use_cache: Whether to use cache (default: True)
    
    Raises:
        AlphaVantageRateLimitError: When API rate limit is exceeded
    
    Returns:
        API response (JSON or CSV string)
    """
    # Determine data type for cache
    data_type_map = {
        'TIME_SERIES_DAILY_ADJUSTED': 'historical_data',
        'TIME_SERIES_INTRADAY': 'stock_quote',
        'OVERVIEW': 'fundamentals',
        'BALANCE_SHEET': 'balance_sheet',
        'INCOME_STATEMENT': 'income_statement',
        'CASH_FLOW': 'cashflow',
        'NEWS_SENTIMENT': 'news',
    }
    data_type = data_type_map.get(function_name, 'stock_quote')
    
    # Try cache first
    if use_cache:
        # Generate cache parameters (exclude API key for security)
        cache_params = {
            'function': function_name,
            'vendor': 'alpha_vantage',
            **{k: v for k, v in params.items() if k != 'apikey'}
        }
        
        cached_data = cache.get(data_type, **cache_params)
        if cached_data is not None:
            logger.debug(f"Cache HIT: {function_name} {params.get('symbol', '')}")
            
            # IMPORTANT: Save news even from cache!
            if function_name == 'NEWS_SENTIMENT':
                logger.info(f"📰 [Cache HIT] Attempting to save cached news to MongoDB...")
                symbol = params.get('tickers') or params.get('symbol')
                news_saver.save_news_from_response(
                    cached_data, 
                    symbol=symbol,
                    source='alpha_vantage'
                )
            
            return cached_data
    
    # Create a copy of params to avoid modifying the original
    api_params = params.copy()
    api_params.update({
        "function": function_name,
        "apikey": get_api_key(),
        "source": "trading_agents",
    })
    
    # Handle entitlement parameter if present in params or global variable
    current_entitlement = globals().get('_current_entitlement')
    entitlement = api_params.get("entitlement") or current_entitlement
    
    if entitlement:
        api_params["entitlement"] = entitlement
    elif "entitlement" in api_params:
        # Remove entitlement if it's None or empty
        api_params.pop("entitlement", None)
    
    logger.debug(f"🌐 API Request: {function_name} {params.get('symbol', '')}")
    response = requests.get(API_BASE_URL, params=api_params)
    response.raise_for_status()

    response_text = response.text
    
    # Check if response is JSON (error responses are typically JSON)
    try:
        response_json = json.loads(response_text)
        # Check for rate limit error
        if "Information" in response_json:
            info_message = response_json["Information"]
            if "rate limit" in info_message.lower() or "api key" in info_message.lower():
                raise AlphaVantageRateLimitError(f"Alpha Vantage rate limit exceeded: {info_message}")
        
        # Cache valid JSON response
        if use_cache:
            cache_params = {
                'function': function_name,
                'vendor': 'alpha_vantage',
                **{k: v for k, v in params.items() if k != 'apikey'}
            }
            cache.set(data_type, response_json, **cache_params)
            logger.debug(f"Cached: {function_name} {params.get('symbol', '')}")
        
        # Save news articles to MongoDB if this is a news request
        if function_name == 'NEWS_SENTIMENT':
            logger.info(f"📰 [API Response] Attempting to save news to MongoDB...")
            logger.info(f"📰 [API Response] Response type: {type(response_json)}, has 'feed': {'feed' in response_json if isinstance(response_json, dict) else 'N/A'}")
            symbol = params.get('tickers') or params.get('symbol')
            logger.info(f"📰 [API Response] Symbol: {symbol}")
            saved_count = news_saver.save_news_from_response(
                response_json, 
                symbol=symbol,
                source='alpha_vantage'
            )
            logger.info(f"📰 [API Response] Saved {saved_count} articles")
        
        return response_json
        
    except json.JSONDecodeError:
        # Response is not JSON (likely CSV data), which is normal
        # Cache CSV response
        if use_cache:
            cache_params = {
                'function': function_name,
                'vendor': 'alpha_vantage',
                **{k: v for k, v in params.items() if k != 'apikey'}
            }
            cache.set(data_type, response_text, **cache_params)
            logger.debug(f"Cached: {function_name} {params.get('symbol', '')}")

    return response_text



def _filter_csv_by_date_range(csv_data: str, start_date: str, end_date: str) -> str:
    """
    Filter CSV data to include only rows within the specified date range.

    Args:
        csv_data: CSV string from Alpha Vantage API
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format

    Returns:
        Filtered CSV string
    """
    if not csv_data or csv_data.strip() == "":
        return csv_data

    try:
        # Parse CSV data
        df = pd.read_csv(StringIO(csv_data))

        # Assume the first column is the date column (timestamp)
        date_col = df.columns[0]
        df[date_col] = pd.to_datetime(df[date_col])

        # Filter by date range
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        filtered_df = df[(df[date_col] >= start_dt) & (df[date_col] <= end_dt)]

        # Convert back to CSV string
        return filtered_df.to_csv(index=False)

    except Exception as e:
        # If filtering fails, return original data with a warning
        logger.warning(f"Failed to filter CSV data by date range: {e}")
        return csv_data
