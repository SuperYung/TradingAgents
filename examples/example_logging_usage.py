"""
Example: Using the TradingAgents Logging System

This example demonstrates how to use the enterprise logging system
in your TradingAgents code.
"""

import os
import sys
import uuid
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tradingagents.utils.logging_manager import get_logger, get_logger_manager


def example_basic_usage():
    """Example 1: Basic logging usage."""
    print("\n=== Example 1: Basic Logging ===\n")
    
    # Get a logger for your module
    logger = get_logger("tradingagents.examples.basic")
    
    # Log at different levels
    logger.debug("This is a debug message (detailed info)")
    logger.info("This is an info message (normal operation)")
    logger.warning("This is a warning (potential issue)")
    logger.error("This is an error (something failed)")
    logger.critical("This is critical (system failure)")


def example_session_tracking():
    """Example 2: Session tracking for analysis."""
    print("\n=== Example 2: Session Tracking ===\n")
    
    logger = get_logger("tradingagents.examples.session")
    session_id = str(uuid.uuid4())
    stock_symbol = "AAPL"
    
    # Start of analysis
    logger.info(
        f"Starting analysis for {stock_symbol}",
        extra={
            'session_id': session_id,
            'stock_symbol': stock_symbol,
            'analysis_type': 'technical'
        }
    )
    
    # During analysis
    time.sleep(0.1)  # Simulate work
    logger.info(
        f"Processing data for {stock_symbol}",
        extra={
            'session_id': session_id,
            'stock_symbol': stock_symbol,
            'progress': 50
        }
    )
    
    # End of analysis
    logger.info(
        f"Analysis complete for {stock_symbol}",
        extra={
            'session_id': session_id,
            'stock_symbol': stock_symbol,
            'duration': 0.1,
            'cost': 0.0023
        }
    )


def example_helper_methods():
    """Example 3: Using helper methods for common patterns."""
    print("\n=== Example 3: Helper Methods ===\n")
    
    logger_manager = get_logger_manager()
    logger = logger_manager.get_logger("tradingagents.examples.helpers")
    session_id = str(uuid.uuid4())
    stock_symbol = "TSLA"
    
    # Log analysis lifecycle
    logger_manager.log_analysis_start(
        logger=logger,
        stock_symbol=stock_symbol,
        analysis_type="fundamental",
        session_id=session_id
    )
    
    time.sleep(0.1)  # Simulate analysis
    
    logger_manager.log_analysis_complete(
        logger=logger,
        stock_symbol=stock_symbol,
        analysis_type="fundamental",
        session_id=session_id,
        duration=0.1,
        cost=0.0015
    )
    
    # Log agent execution
    logger_manager.log_agent_start(
        logger=logger,
        agent_name="market_analyst",
        stock_symbol=stock_symbol,
        session_id=session_id
    )
    
    time.sleep(0.05)  # Simulate agent work
    
    logger_manager.log_agent_complete(
        logger=logger,
        agent_name="market_analyst",
        stock_symbol=stock_symbol,
        session_id=session_id,
        duration=0.05,
        success=True,
        result_length=1500
    )
    
    # Log token usage
    logger_manager.log_token_usage(
        logger=logger,
        provider="openai",
        model="gpt-4",
        input_tokens=1000,
        output_tokens=500,
        cost=0.0023,
        session_id=session_id
    )


def example_error_handling():
    """Example 4: Error logging with tracebacks."""
    print("\n=== Example 4: Error Handling ===\n")
    
    logger = get_logger("tradingagents.examples.errors")
    
    try:
        # Simulate an error
        result = 10 / 0
    except Exception as e:
        # Log with traceback
        logger.error(
            f"Failed to calculate result: {e}",
            exc_info=True  # This includes the full traceback
        )
        
    # Log agent error
    logger_manager = get_logger_manager()
    session_id = str(uuid.uuid4())
    
    logger_manager.log_agent_error(
        logger=logger,
        agent_name="test_agent",
        stock_symbol="TEST",
        session_id=session_id,
        duration=1.5,
        error="Simulated agent failure"
    )


def example_agent_integration():
    """Example 5: Full agent integration pattern."""
    print("\n=== Example 5: Agent Integration ===\n")
    
    logger = get_logger("tradingagents.agents.example_analyst")
    logger_manager = get_logger_manager()
    session_id = str(uuid.uuid4())
    stock_symbol = "NVDA"
    agent_name = "example_analyst"
    
    # Start agent execution
    start_time = time.time()
    logger_manager.log_agent_start(
        logger=logger,
        agent_name=agent_name,
        stock_symbol=stock_symbol,
        session_id=session_id
    )
    
    try:
        # Simulate agent work
        logger.debug(f"Fetching data for {stock_symbol}")
        time.sleep(0.1)
        
        logger.debug(f"Analyzing data for {stock_symbol}")
        time.sleep(0.1)
        
        logger.debug(f"Generating report for {stock_symbol}")
        time.sleep(0.1)
        
        result = f"Analysis report for {stock_symbol}"
        duration = time.time() - start_time
        
        # Log successful completion
        logger_manager.log_agent_complete(
            logger=logger,
            agent_name=agent_name,
            stock_symbol=stock_symbol,
            session_id=session_id,
            duration=duration,
            success=True,
            result_length=len(result)
        )
        
        return result
        
    except Exception as e:
        # Log error
        duration = time.time() - start_time
        logger_manager.log_agent_error(
            logger=logger,
            agent_name=agent_name,
            stock_symbol=stock_symbol,
            session_id=session_id,
            duration=duration,
            error=str(e)
        )
        raise


def main():
    """Run all examples."""
    print("="*70)
    print("TradingAgents Logging System - Usage Examples")
    print("="*70)
    
    examples = [
        example_basic_usage,
        example_session_tracking,
        example_helper_methods,
        example_error_handling,
        example_agent_integration
    ]
    
    for example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"Example {example_func.__name__} raised expected error: {e}")
    
    print("\n" + "="*70)
    print("Examples Complete!")
    print("="*70)
    print("\nCheck the log files:")
    print("  - ./logs/tradingagents.log (all messages)")
    print("  - ./logs/error.log (warnings and errors only)")
    print("\nNote: Colored output appears in the console if your terminal supports it.")
    print("="*70)


if __name__ == "__main__":
    # Change to project root for log files
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Run examples
    main()

