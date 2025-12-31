#!/usr/bin/env python3
"""
Example: Using TradingAgents with Agent Logging

This script demonstrates how to run TradingAgents with logging enabled
to capture all agent prompts and LLM responses for study.
"""

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def main():
    print("=" * 80)
    print("TradingAgents with Agent Logging Example")
    print("=" * 80)
    
    # Create configuration
    config = DEFAULT_CONFIG.copy()
    
    # Customize if needed
    # config["deep_think_llm"] = "gemini-2.5-pro"
    # config["quick_think_llm"] = "gemini-2.5-flash"
    
    print("\n1. Initializing TradingAgents with logging enabled...")
    
    # Initialize with logging enabled (default)
    ta = TradingAgentsGraph(
        selected_analysts=["market", "news", "fundamentals"],  # Select analysts
        debug=False,  # Set to True to see real-time output
        config=config,
        enable_logging=True,  # Enable agent logging
        log_dir=None  # Use default ./agent_logs directory
    )
    
    # The log directory is printed automatically when the graph is created
    log_path = ta.get_log_directory()
    
    print(f"\n2. Running analysis for AAPL on 2024-05-10...")
    print("   (This may take 1-2 minutes...)")
    
    # Run the analysis
    final_state, decision = ta.propagate("AAPL", "2024-05-10")
    
    print(f"\n3. Analysis complete!")
    print(f"   Decision: {decision}")
    
    print(f"\n4. Agent logs have been saved!")
    print(f"   Location: {log_path}")
    print(f"\n   To view the logs:")
    print(f"   - Open in browser: open {log_path}/index.html")
    print(f"   - Read summary:    cat {log_path}/00_SUMMARY.md")
    print(f"   - View directory:  open {log_path}")
    
    print("\n" + "=" * 80)
    print("What's in the logs:")
    print("=" * 80)
    
    # List the log files
    import glob
    log_files = sorted(glob.glob(os.path.join(log_path, "*.md")))
    
    for log_file in log_files:
        filename = os.path.basename(log_file)
        if filename != "00_SUMMARY.md":
            agent_name = filename.split("_")[1]
            print(f"  ✓ {agent_name:25s} → {filename}")
    
    print("\n" + "=" * 80)
    print("Study your agents:")
    print("=" * 80)
    print(f"  1. Open the HTML index: open {log_path}/index.html")
    print(f"  2. Read individual agent logs (markdown files)")
    print(f"  3. See what prompts each agent received")
    print(f"  4. Understand what tools they called and why")
    print(f"  5. Review their reasoning and final decisions")
    print("\n  See AGENT_LOGGING_GUIDE.md for more details.")
    print("=" * 80)


if __name__ == "__main__":
    main()

