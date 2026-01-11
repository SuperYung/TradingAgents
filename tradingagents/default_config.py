import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_dir": "/Users/yluo/Documents/Code/ScAI/FR1-data",
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # LLM settings
    "llm_provider": "google",
    "deep_think_llm": "gemini-2.5-pro",
    "quick_think_llm": "gemini-2.5-flash",
    "backend_url": "",
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # Redis configuration (L2 Cache)
    "redis_enabled": os.getenv("REDIS_ENABLED", "false").lower() == "true",
    "redis_host": os.getenv("REDIS_HOST", "localhost"),
    "redis_port": int(os.getenv("REDIS_PORT", "6379")),
    "redis_db": int(os.getenv("REDIS_DB", "0")),
    "redis_password": os.getenv("REDIS_PASSWORD", ""),
    # MongoDB configuration (L3 Cache + Persistent Storage)
    "mongodb_enabled": os.getenv("MONGODB_ENABLED", "false").lower() == "true",
    "mongodb_host": os.getenv("MONGODB_HOST", "localhost"),
    "mongodb_port": int(os.getenv("MONGODB_PORT", "27017")),
    "mongodb_database": os.getenv("MONGODB_DATABASE", "tradingagents"),
    "mongodb_save_analyses": os.getenv("MONGODB_SAVE_ANALYSES", "true").lower() == "true",
    "mongodb_save_news": os.getenv("MONGODB_SAVE_NEWS", "true").lower() == "true",
    "mongodb_track_usage": os.getenv("MONGODB_TRACK_USAGE", "true").lower() == "true",
    # Data vendor configuration
    # Category-level configuration (default for all tools in category)
    "data_vendors": {
        "core_stock_apis": "yfinance",       # Options: yfinance, alpha_vantage, local
        "technical_indicators": "yfinance",  # Options: yfinance, alpha_vantage, local
        "fundamental_data": "alpha_vantage", # Options: openai, alpha_vantage, local
        "news_data": "alpha_vantage",        # Options: openai, alpha_vantage, google, local
    },
    # Tool-level configuration (takes precedence over category-level)
    "tool_vendors": {
        # Example: "get_stock_data": "alpha_vantage",  # Override category default
        # Example: "get_news": "openai",               # Override category default
        "tool_vendors": {
            "get_global_news": "google"
        }
    },
}
