import os

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_dir": os.getenv("TRADINGAGENTS_DATA_DIR", os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "data"
    )),
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # LLM settings - Default to Google Gemini Pro (free tier)
    "llm_provider": "google",  # Options: "google", "openai", "anthropic", "ollama"
    "deep_think_llm": "gemini-2.5-pro",  # Gemini Pro for deep thinking
    "quick_think_llm": "gemini-2.5-flash",  # Gemini Flash for quick responses
    "backend_url": "",  # Not needed for Google, set for OpenAI/Ollama
    # Rate limiting settings
    "rate_limit_max_retries": 5,
    "rate_limit_wait_exponential_multiplier": 1,
    "rate_limit_wait_exponential_max": 60,
    # Cache settings
    "cache_ttl_seconds": 3600,  # 1 hour cache TTL
    "cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/cache",
    ),
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # Data vendor configuration - All free tier
    # Category-level configuration (default for all tools in category)
    "data_vendors": {
        "core_stock_apis": "yfinance",       # Free: Yahoo Finance
        "technical_indicators": "yfinance",  # Free: Yahoo Finance
        "fundamental_data": "alpha_vantage", # Free: Yahoo Finance (migrated from alpha_vantage)
        "news_data": "yfinance",             # Free: Yahoo Finance (fast and reliable)
    },
    # Tool-level configuration (takes precedence over category-level)
    "tool_vendors": {
        # Example: "get_stock_data": "yfinance",
        # Example: "get_news": "google",
    },
}
