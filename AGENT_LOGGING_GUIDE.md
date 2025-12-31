# Agent Logging Guide

## Overview

The Agent Logging system captures all LLM interactions (prompts and responses) from every agent in the TradingAgents system. This helps you study how each agent makes decisions and understand the reasoning process.

## What Gets Logged

For each agent interaction, the system logs:

1. **Agent Name** - Which agent made the call (e.g., `news_analyst`, `trader`, `bull_researcher`)
2. **System Prompt** - The instructions given to the agent
3. **Input Messages** - The context and data provided
4. **LLM Response** - The raw response from the LLM
5. **Tool Calls** - Any tools the agent invoked (with arguments)
6. **Final Output** - The processed report or decision
7. **Metadata** - Additional context (ticker, date, debate round, etc.)
8. **Timestamp** - When the interaction occurred

## Agents That Are Logged

All agents with LLM interactions are logged:

- **Analysts**: `news_analyst`, `market_analyst`, `social_media_analyst`, `fundamentals_analyst`
- **Researchers**: `bull_researcher`, `bear_researcher`
- **Managers**: `research_manager`, `risk_manager`
- **Trader**: `trader`

## How to Enable Logging

### Basic Usage

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph

# Logging is ENABLED by default
ta = TradingAgents Graph(
    debug=True,
    enable_logging=True  # This is the default
)

# Run your analysis
_, decision = ta.propagate("AAPL", "2024-05-10")

# Logs are automatically saved and indexed
# Location will be printed when the graph is created
```

### Custom Log Directory

```python
ta = TradingAgentsGraph(
    enable_logging=True,
    log_dir="/path/to/my/logs"  # Custom directory
)
```

### Disable Logging

```python
ta = TradingAgentsGraph(
    enable_logging=False  # Turn off logging
)
```

## Log Output Structure

Logs are saved in: `./agent_logs/YYYYMMDD_HHMMSS/`

Each run creates a new timestamped directory with:

```
agent_logs/
└── 20241230_143025/           # Run timestamp
    ├── 00_SUMMARY.md          # Quick overview of all interactions
    ├── index.html             # Browsable index (open in browser)
    ├── 001_news_analyst_2024-12-30T14-30-26.json    # Raw JSON data
    ├── 001_news_analyst_2024-12-30T14-30-26.md      # Human-readable markdown
    ├── 002_market_analyst_2024-12-30T14-30-35.json
    ├── 002_market_analyst_2024-12-30T14-30-35.md
    ├── 003_fundamentals_analyst_2024-12-30T14-30-45.json
    ├── 003_fundamentals_analyst_2024-12-30T14-30-45.md
    ├── 004_social_media_analyst_2024-12-30T14-30-50.json
    ├── 004_social_media_analyst_2024-12-30T14-30-50.md
    ├── 005_bull_researcher_2024-12-30T14-31-00.json
    ├── 005_bull_researcher_2024-12-30T14-31-00.md
    ├── 006_bear_researcher_2024-12-30T14-31-10.json
    ├── 006_bear_researcher_2024-12-30T14-31-10.md
    ├── 007_research_manager_2024-12-30T14-31-20.json
    ├── 007_research_manager_2024-12-30T14-31-20.md
    ├── 008_trader_2024-12-30T14-31-30.json
    ├── 008_trader_2024-12-30T14-31-30.md
    ├── 009_risk_manager_2024-12-30T14-31-40.json
    └── 009_risk_manager_2024-12-30T14-31-40.md
```

## Reading the Logs

### Method 1: Open in Browser (Easiest)

```bash
# After running your analysis
cd agent_logs/20241230_143025/
open index.html  # macOS
# or
xdg-open index.html  # Linux
# or just double-click index.html in Windows
```

The HTML index provides:
- Clickable list of all interactions
- Links to both JSON and Markdown versions
- Timestamps and agent names

### Method 2: Read Markdown Files

Markdown files (`.md`) are human-readable and include:

```markdown
# news_analyst - Interaction 1

**Timestamp:** 2024-12-30T14:30:26

## Metadata
- **ticker:** AAPL
- **trade_date:** 2024-05-10
- **tools_available:** get_news, get_global_news

## System Prompt
```
You are a news researcher tasked with analyzing recent news...
```

## Input Messages

### Message 1 (user)
```
Please analyze the news for AAPL...
```

## Tool Calls

### Tool Call 1
**Function:** get_news

**Arguments:**
```json
{
  "ticker": "AAPL",
  "start_date": "2024-05-01",
  "end_date": "2024-05-10"
}
```

## LLM Response
```
Based on my analysis of recent news for Apple Inc...
```

## Final Output / Report
The news analyst has identified several key trends...
```

### Method 3: Parse JSON Programmatically

```python
import json
from pathlib import Path

log_dir = Path("agent_logs/20241230_143025")

# Read a specific interaction
with open(log_dir / "001_news_analyst_2024-12-30T14-30-26.json") as f:
    interaction = json.load(f)

print(f"Agent: {interaction['agent_name']}")
print(f"System Prompt: {interaction['system_prompt']}")
print(f"Response: {interaction['llm_response']['content']}")
print(f"Tool Calls: {len(interaction['tool_calls'])}")
```

### Method 4: Read Summary

The `00_SUMMARY.md` file provides a quick overview:

```markdown
# Agent Interactions Log - Run 20241230_143025

**Started:** 2024-12-30 14:30:25

---

## 1. news_analyst
- **Time:** 2024-12-30T14:30:26
- **ticker:** AAPL
- **trade_date:** 2024-05-10
- **Tool Calls:** 2
- **Has Output:** Yes

## 2. market_analyst
- **Time:** 2024-12-30T14:30:35
- **ticker:** AAPL
- **trade_date:** 2024-05-10
- **Tool Calls:** 2
- **Has Output:** Yes

...
```

## Example: Studying Agent Decisions

### Study how the news analyst processes information:

```bash
# Open the news analyst's markdown file
cat agent_logs/20241230_143025/001_news_analyst_*.md
```

You'll see:
1. **What instructions the agent received** (System Prompt)
2. **What tools it decided to call** (Tool Calls)
3. **What it learned** (LLM Response with reasoning)
4. **Its final report** (Final Output)

### Compare Bull vs Bear arguments:

```bash
# View bull researcher's argument
cat agent_logs/20241230_143025/*bull_researcher*.md

# View bear researcher's argument
cat agent_logs/20241230_143025/*bear_researcher*.md
```

### Trace the decision flow:

1. Analysts gather data → Look at `001-004_*analyst*.md`
2. Researchers debate → Look at `005-006_*researcher*.md`
3. Manager decides → Look at `007_research_manager*.md`
4. Trader proposes → Look at `008_trader*.md`
5. Risk manager finalizes → Look at `009_risk_manager*.md`

## Getting Log Location Programmatically

```python
ta = TradingAgentsGraph(enable_logging=True)
_, decision = ta.propagate("AAPL", "2024-05-10")

# Get the log directory path
log_path = ta.get_log_directory()
print(f"Logs saved to: {log_path}")

# Open in your file browser
import os
os.system(f"open {log_path}")  # macOS
# os.system(f"explorer {log_path}")  # Windows
# os.system(f"xdg-open {log_path}")  # Linux
```

## Advanced: Analyzing Logs

### Find all interactions for a specific ticker:

```bash
cd agent_logs/20241230_143025
grep -l "AAPL" *.json
```

### Extract all tool calls:

```python
import json
from pathlib import Path

log_dir = Path("agent_logs/20241230_143025")

for json_file in sorted(log_dir.glob("*.json")):
    with open(json_file) as f:
        data = json.load(f)
    
    if data.get("tool_calls"):
        print(f"\n{data['agent_name']}:")
        for tc in data['tool_calls']:
            print(f"  - {tc['name']}({tc['args']})")
```

### Compare performance across runs:

```python
from pathlib import Path
import json

# Compare decisions across multiple runs
runs = sorted(Path("agent_logs").iterdir())

for run in runs[-5:]:  # Last 5 runs
    summary = run / "00_SUMMARY.md"
    if summary.exists():
        print(f"\n{run.name}:")
        # Parse and compare...
```

## Tips for Effective Study

1. **Start with the Summary** - Get a quick overview first
2. **Follow the Flow** - Read agents in chronological order (001 → 002 → ...)
3. **Focus on Decisions** - Look at managers and trader for key decisions
4. **Check Tool Calls** - See what data each agent requested
5. **Compare Prompts** - Understand what instructions drive each agent
6. **Study Debates** - Bull/Bear researchers show both sides of analysis

## Troubleshooting

### Logs not being created?

Check that logging is enabled:
```python
ta = TradingAgentsGraph(enable_logging=True)  # Explicitly enable
```

### Can't find log directory?

Get the path programmatically:
```python
log_path = ta.get_log_directory()
print(f"Logs are at: {log_path}")
```

### Logs too large?

Logs can be large for complex analyses. To manage:
- Disable logging for production runs
- Clean old logs periodically: `rm -rf agent_logs/202412*`
- Archive important runs: `tar -czf aapl_analysis.tar.gz agent_logs/20241230_143025/`

## Performance Impact

Logging adds minimal overhead:
- **~10-50ms** per interaction (file I/O)
- **~5-10MB** per full workflow run
- **No impact** on LLM call speed (logged after response)

For production/batch processing, consider disabling logging to save disk space.

---

**Happy studying! The logs give you complete visibility into how your agents think and make decisions.** 🔍

