# Quick Start Guide - Free Tier TradingAgents

Get started with TradingAgents using 100% free APIs in under 5 minutes!

## Prerequisites

- Python 3.8+
- Google API Key (free from [Google AI Studio](https://makersuite.google.com/app/apikey))

## Installation

### 1. Clone & Install

```bash
cd TradingAgents
pip install -r requirements.txt
```

### 2. Set Up API Key

Create a `.env` file:

```bash
echo "GOOGLE_API_KEY=your-api-key-here" > .env
```

Or export directly:

```bash
export GOOGLE_API_KEY='your-api-key-here'
```

### 3. Verify Setup

```bash
python tests/test_setup.py
```

Expected output:
```
✓ PASS: Imports
✓ PASS: Environment Variables
✓ PASS: Configuration
✓ PASS: Cache Utilities
✓ PASS: Rate Limiting
✓ PASS: Memory System
✓ PASS: Yahoo Finance

Passed: 7/7
✓ All tests passed! System is ready to use.
```

## Usage

### Basic Example

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Use default config (Google Gemini + Yahoo Finance - FREE!)
config = DEFAULT_CONFIG.copy()

# Initialize
ta = TradingAgentsGraph(debug=True, config=config)

# Run analysis
_, decision = ta.propagate("AAPL", "2024-05-10")
print(f"Decision: {decision}")
```

### Custom Configuration

```python
# Customize settings
config = DEFAULT_CONFIG.copy()
config["max_debate_rounds"] = 2  # More thorough analysis
config["cache_ttl_seconds"] = 7200  # 2-hour cache

# Select specific analysts
ta = TradingAgentsGraph(
    selected_analysts=["market", "news"],  # Just these two
    debug=True,
    config=config
)
```

### Test Individual Components

```bash
# Test agents
python tests/test_agents.py

# Full integration test
python tests/test_integration.py
```

## What's Different?

### Before (Paid)
- OpenAI API: $0.15-$2.50 per 1M tokens
- Alpha Vantage: $50/month
- Total: ~$50-100/month

### After (Free)
- Google Gemini: FREE
- Yahoo Finance: FREE
- Total: **$0/month** 🎉

### Performance Improvements
- **3-100x faster** with caching
- Automatic retries on rate limits
- Better error handling

## Common Commands

```bash
# Clear cache
python -c "from tradingagents.dataflows.cache_utils import clear_cache; clear_cache()"

# Run tests
python tests/test_setup.py       # Quick validation
python tests/test_agents.py      # Agent tests
python tests/test_integration.py # Full workflow

# Check cache size
du -sh tradingagents/dataflows/cache/

# View logs
ls -la results/
```

## Example Output

```
Testing AAPL on 2024-05-10...

Market Analyst: Analyzing technical indicators...
✓ RSI: 65.3 (neutral)
✓ MACD: Bullish crossover
✓ Volume: Above average

News Analyst: Analyzing recent news...
✓ Positive earnings report
✓ New product announcement
✓ Analyst upgrades

Research Manager: Synthesizing analysis...
Bull case: Strong technicals, positive catalysts
Bear case: High valuation, market uncertainty

Risk Manager: Assessing risk...
Position size: 2% of portfolio
Stop loss: -5%

Final Decision: BUY (Confidence: 75%)
```

## Configuration Options

### LLM Models

```python
# Fast & Free (Recommended)
config["deep_think_llm"] = "gemini-1.5-pro"
config["quick_think_llm"] = "gemini-1.5-flash"

# Premium (if you have OpenAI)
config["llm_provider"] = "openai"
config["deep_think_llm"] = "gpt-4o"
config["quick_think_llm"] = "gpt-4o-mini"
```

### Data Vendors

```python
# All free (default)
config["data_vendors"] = {
    "core_stock_apis": "yfinance",
    "technical_indicators": "yfinance",
    "fundamental_data": "yfinance",
    "news_data": "google",
}
```

### Caching

```python
# Adjust cache duration
config["cache_ttl_seconds"] = 3600  # 1 hour (default)
config["cache_ttl_seconds"] = 300   # 5 minutes (more fresh)
config["cache_ttl_seconds"] = 7200  # 2 hours (less API calls)
```

### Rate Limiting

```python
# Adjust retry behavior
config["rate_limit_max_retries"] = 5      # Max retries
config["rate_limit_wait_exponential_max"] = 60  # Max wait (seconds)
```

## Troubleshooting

### "GOOGLE_API_KEY not set"

```bash
export GOOGLE_API_KEY='your-key-here'
```

### "Rate limit exceeded"

Wait a minute or increase cache TTL:

```python
config["cache_ttl_seconds"] = 7200  # 2 hours
```

### Cache not working

Clear and retry:

```bash
rm -rf tradingagents/dataflows/cache/
python your_script.py
```

### Import errors

Reinstall dependencies:

```bash
pip install -r requirements.txt --force-reinstall
```

## Next Steps

1. ✅ Read [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for detailed migration info
2. ✅ Check [IMPROVEMENTS.md](IMPROVEMENTS.md) for architecture recommendations
3. ✅ Explore example notebooks (coming soon)
4. ✅ Join community discussions

## Support

- 📚 Documentation: See MIGRATION_GUIDE.md
- 🐛 Issues: Check logs in `./results/`
- 💡 Questions: Review test files for examples

## Summary

You're now running a **production-grade trading agent system for FREE**! 🚀

Key features:
- ✅ Zero cost (Google Gemini + Yahoo Finance)
- ✅ Fast (3-100x with caching)
- ✅ Reliable (automatic retries)
- ✅ Testable (comprehensive test suite)
- ✅ Well-documented

Happy trading! 📈

