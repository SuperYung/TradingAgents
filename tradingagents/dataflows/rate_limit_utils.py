"""
Rate limiting utilities for TradingAgents.
Implements retry logic with exponential backoff for API calls.
"""

from functools import wraps
from typing import Callable, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
import logging
from .config import get_config


# Setup logging for rate limiting
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_retry_decorator(
    max_retries: Optional[int] = None,
    multiplier: Optional[int] = None,
    max_wait: Optional[int] = None,
    retry_on_exceptions: tuple = (Exception,)
):
    """
    Create a retry decorator with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts. If None, uses config default.
        multiplier: Exponential backoff multiplier. If None, uses config default.
        max_wait: Maximum wait time in seconds. If None, uses config default.
        retry_on_exceptions: Tuple of exception types to retry on.
    
    Returns:
        Retry decorator function
    """
    config = get_config()
    
    # Get values from config or use provided values
    max_retries = max_retries if max_retries is not None else config.get("rate_limit_max_retries", 5)
    multiplier = multiplier if multiplier is not None else config.get("rate_limit_wait_exponential_multiplier", 1)
    max_wait = max_wait if max_wait is not None else config.get("rate_limit_wait_exponential_max", 60)
    
    return retry(
        stop=stop_after_attempt(max_retries),
        wait=wait_exponential(multiplier=multiplier, max=max_wait),
        retry=retry_if_exception_type(retry_on_exceptions),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO)
    )


def rate_limited(
    max_retries: Optional[int] = None,
    multiplier: Optional[int] = None,
    max_wait: Optional[int] = None,
    retry_on_exceptions: tuple = None
):
    """
    Decorator to add rate limiting with retry logic to a function.
    
    Automatically retries on common rate limit exceptions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        multiplier: Exponential backoff multiplier
        max_wait: Maximum wait time in seconds
        retry_on_exceptions: Tuple of exception types to retry on
    
    Example:
        @rate_limited(max_retries=3, multiplier=2, max_wait=30)
        def call_api(params):
            # API call that might be rate limited
            return api.fetch(params)
    """
    # Default exceptions to retry on (rate limits, timeouts, etc.)
    if retry_on_exceptions is None:
        retry_on_exceptions = (
            Exception,  # Generic catch-all
        )
        
        # Try to import specific exceptions
        try:
            from openai import RateLimitError, APITimeoutError, APIConnectionError
            retry_on_exceptions = (RateLimitError, APITimeoutError, APIConnectionError, Exception)
        except ImportError:
            pass
        
        try:
            from google.api_core.exceptions import ResourceExhausted, DeadlineExceeded
            retry_on_exceptions = retry_on_exceptions + (ResourceExhausted, DeadlineExceeded)
        except ImportError:
            pass
    
    def decorator(func: Callable) -> Callable:
        retry_dec = get_retry_decorator(
            max_retries=max_retries,
            multiplier=multiplier,
            max_wait=max_wait,
            retry_on_exceptions=retry_on_exceptions
        )
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return retry_dec(func)(*args, **kwargs)
        
        return wrapper
    
    return decorator


# Specialized decorators for different API types

def llm_rate_limited(max_retries: Optional[int] = None):
    """
    Decorator specifically for LLM API calls.
    Handles common LLM rate limit errors.
    """
    retry_exceptions = (Exception,)
    
    # Add provider-specific exceptions
    try:
        from openai import RateLimitError, APITimeoutError, APIConnectionError, APIError
        retry_exceptions = (RateLimitError, APITimeoutError, APIConnectionError, APIError)
    except ImportError:
        pass
    
    try:
        from google.api_core.exceptions import ResourceExhausted, DeadlineExceeded, GoogleAPIError
        retry_exceptions = retry_exceptions + (ResourceExhausted, DeadlineExceeded, GoogleAPIError)
    except ImportError:
        pass
    
    return rate_limited(
        max_retries=max_retries,
        multiplier=2,
        max_wait=120,  # LLM calls might need longer waits
        retry_on_exceptions=retry_exceptions
    )


def data_api_rate_limited(max_retries: Optional[int] = None):
    """
    Decorator specifically for data API calls (Yahoo Finance, Alpha Vantage, etc.).
    More aggressive retries for data APIs.
    """
    return rate_limited(
        max_retries=max_retries if max_retries is not None else 3,
        multiplier=1,
        max_wait=30,
        retry_on_exceptions=(Exception,)
    )


def embedding_rate_limited(max_retries: Optional[int] = None):
    """
    Decorator specifically for embedding API calls.
    Handles rate limits for embedding generation.
    """
    retry_exceptions = (Exception,)
    
    try:
        from openai import RateLimitError, APITimeoutError
        retry_exceptions = (RateLimitError, APITimeoutError)
    except ImportError:
        pass
    
    try:
        from google.api_core.exceptions import ResourceExhausted
        retry_exceptions = retry_exceptions + (ResourceExhausted,)
    except ImportError:
        pass
    
    return rate_limited(
        max_retries=max_retries if max_retries is not None else 5,
        multiplier=1,
        max_wait=60,
        retry_on_exceptions=retry_exceptions
    )


if __name__ == "__main__":
    import time
    
    # Example usage
    @rate_limited(max_retries=3, multiplier=1, max_wait=10)
    def flaky_function(should_fail=True):
        """Simulates a function that might fail due to rate limiting."""
        print(f"Attempting function call at {time.time()}")
        if should_fail:
            raise Exception("Rate limit exceeded!")
        return "Success!"
    
    # Test the retry logic
    print("Testing rate limited function (will fail and retry):")
    try:
        result = flaky_function(should_fail=True)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed after all retries: {e}")
    
    print("\nTesting with success:")
    result = flaky_function(should_fail=False)
    print(f"Result: {result}")

