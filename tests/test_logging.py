#!/usr/bin/env python3
"""
Test script for the TradingAgents logging system.
Tests all major logging features including rotation, colored output, session tracking, etc.
"""

import os
import sys
import time
import uuid
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tradingagents.utils.logging_manager import (
    get_logger,
    get_logger_manager,
    setup_logging,
    TradingAgentsLogger
)


def test_basic_logging():
    """Test basic logging functionality."""
    print("\n" + "="*60)
    print("TEST 1: Basic Logging")
    print("="*60)
    
    logger = get_logger("tradingagents.test.basic")
    
    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    logger.critical("This is a CRITICAL message")
    
    print("✅ Basic logging test complete")


def test_session_tracking():
    """Test session tracking with extra fields."""
    print("\n" + "="*60)
    print("TEST 2: Session Tracking")
    print("="*60)
    
    logger = get_logger("tradingagents.test.session")
    session_id = str(uuid.uuid4())
    
    logger.info(
        "Starting analysis",
        extra={
            'session_id': session_id,
            'stock_symbol': 'AAPL',
            'analysis_type': 'technical'
        }
    )
    
    logger.info(
        "Analysis in progress",
        extra={
            'session_id': session_id,
            'stock_symbol': 'AAPL',
            'progress': 50
        }
    )
    
    logger.info(
        "Analysis complete",
        extra={
            'session_id': session_id,
            'stock_symbol': 'AAPL',
            'duration': 12.5,
            'cost': 0.0023
        }
    )
    
    print(f"✅ Session tracking test complete (session_id: {session_id[:8]}...)")


def test_helper_methods():
    """Test specialized helper methods."""
    print("\n" + "="*60)
    print("TEST 3: Helper Methods")
    print("="*60)
    
    logger_manager = get_logger_manager()
    logger = logger_manager.get_logger("tradingagents.test.helpers")
    session_id = str(uuid.uuid4())
    
    # Test analysis logging
    logger_manager.log_analysis_start(
        logger=logger,
        stock_symbol="TSLA",
        analysis_type="fundamental",
        session_id=session_id
    )
    
    time.sleep(0.1)  # Simulate work
    
    logger_manager.log_analysis_complete(
        logger=logger,
        stock_symbol="TSLA",
        analysis_type="fundamental",
        session_id=session_id,
        duration=0.1,
        cost=0.0015
    )
    
    # Test agent logging
    logger_manager.log_agent_start(
        logger=logger,
        agent_name="market_analyst",
        stock_symbol="TSLA",
        session_id=session_id
    )
    
    logger_manager.log_agent_complete(
        logger=logger,
        agent_name="market_analyst",
        stock_symbol="TSLA",
        session_id=session_id,
        duration=0.05,
        success=True,
        result_length=1500
    )
    
    # Test token usage logging
    logger_manager.log_token_usage(
        logger=logger,
        provider="openai",
        model="gpt-4",
        input_tokens=1000,
        output_tokens=500,
        cost=0.0023,
        session_id=session_id
    )
    
    print("✅ Helper methods test complete")


def test_error_logging():
    """Test error logging and exception handling."""
    print("\n" + "="*60)
    print("TEST 4: Error Logging")
    print("="*60)
    
    logger = get_logger("tradingagents.test.errors")
    
    # Test error logging
    logger.error("This is an error message")
    
    # Test exception logging
    try:
        raise ValueError("Test exception for logging")
    except Exception as e:
        logger.error(f"Caught exception: {e}", exc_info=True)
    
    # Test agent error helper
    logger_manager = get_logger_manager()
    session_id = str(uuid.uuid4())
    
    logger_manager.log_agent_error(
        logger=logger,
        agent_name="test_agent",
        stock_symbol="TEST",
        session_id=session_id,
        duration=1.5,
        error="Simulated error for testing"
    )
    
    print("✅ Error logging test complete")
    print("   Check ./logs/error.log for error messages")


def test_file_existence():
    """Test that log files are created."""
    print("\n" + "="*60)
    print("TEST 5: Log File Existence")
    print("="*60)
    
    log_dir = Path("./logs")
    
    # Check if log directory exists
    if log_dir.exists():
        print(f"✅ Log directory exists: {log_dir.absolute()}")
    else:
        print(f"❌ Log directory does not exist: {log_dir.absolute()}")
        return
    
    # Check for log files
    log_files = {
        "tradingagents.log": "Main log file",
        "error.log": "Error log file"
    }
    
    for filename, description in log_files.items():
        filepath = log_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"✅ {description} exists: {filename} ({size} bytes)")
        else:
            print(f"⚠️  {description} not found: {filename}")


def test_log_rotation():
    """Test log rotation (simulated by writing many logs)."""
    print("\n" + "="*60)
    print("TEST 6: Log Rotation (Simulated)")
    print("="*60)
    
    logger = get_logger("tradingagents.test.rotation")
    
    print("Writing 100 log messages...")
    for i in range(100):
        logger.info(f"Log message {i+1} - " + "x" * 100)
    
    print("✅ Log rotation test complete")
    print("   Note: To fully test rotation, you need to exceed 10MB")


def test_colored_output():
    """Test colored console output."""
    print("\n" + "="*60)
    print("TEST 7: Colored Console Output")
    print("="*60)
    
    logger = get_logger("tradingagents.test.colors")
    
    print("If you see colored output below, colored logging is working:")
    logger.debug("DEBUG (should be cyan)")
    logger.info("INFO (should be green)")
    logger.warning("WARNING (should be yellow)")
    logger.error("ERROR (should be red)")
    logger.critical("CRITICAL (should be magenta)")
    
    print("✅ Colored output test complete")


def test_custom_config():
    """Test custom configuration."""
    print("\n" + "="*60)
    print("TEST 8: Custom Configuration")
    print("="*60)
    
    # Create a temporary directory for test logs
    with tempfile.TemporaryDirectory() as tmpdir:
        custom_config = {
            'level': 'DEBUG',
            'format': {
                'console': '%(levelname)s - %(message)s',
                'file': '%(asctime)s | %(message)s'
            },
            'handlers': {
                'console': {
                    'enabled': True,
                    'colored': False,  # Disable colors for this test
                    'level': 'DEBUG'
                },
                'file': {
                    'enabled': True,
                    'level': 'DEBUG',
                    'max_size': '1MB',
                    'backup_count': 3,
                    'directory': tmpdir
                },
                'error': {
                    'enabled': True,
                    'level': 'WARNING',
                    'directory': tmpdir,
                    'filename': 'custom_errors.log'
                },
                'structured': {
                    'enabled': False
                }
            },
            'loggers': {
                'tradingagents': {'level': 'DEBUG'}
            }
        }
        
        # Create a new logger manager with custom config
        custom_manager = TradingAgentsLogger(custom_config)
        custom_logger = custom_manager.get_logger("tradingagents.test.custom")
        
        custom_logger.debug("Custom config DEBUG message")
        custom_logger.info("Custom config INFO message")
        custom_logger.warning("Custom config WARNING message")
        
        # Check if files were created in tmpdir
        tmpdir_path = Path(tmpdir)
        files = list(tmpdir_path.glob("*.log"))
        
        if files:
            print(f"✅ Custom configuration test complete")
            print(f"   Created {len(files)} log file(s) in temp directory")
        else:
            print("❌ No log files created with custom config")


def test_environment_variables():
    """Test environment variable configuration."""
    print("\n" + "="*60)
    print("TEST 9: Environment Variables")
    print("="*60)
    
    # Set environment variables
    os.environ['TRADINGAGENTS_LOG_LEVEL'] = 'DEBUG'
    os.environ['TRADINGAGENTS_LOG_DIR'] = './logs'
    
    # Create a new logger manager that will read env vars
    env_manager = TradingAgentsLogger()
    env_logger = env_manager.get_logger("tradingagents.test.env")
    
    env_logger.debug("Environment variable configuration working")
    env_logger.info("Log level set from TRADINGAGENTS_LOG_LEVEL")
    
    print("✅ Environment variable test complete")


def test_performance():
    """Test logging performance."""
    print("\n" + "="*60)
    print("TEST 10: Performance")
    print("="*60)
    
    logger = get_logger("tradingagents.test.performance")
    
    # Test logging speed
    num_logs = 1000
    start_time = time.time()
    
    for i in range(num_logs):
        logger.info(f"Performance test message {i}")
    
    duration = time.time() - start_time
    rate = num_logs / duration
    
    print(f"✅ Performance test complete")
    print(f"   Logged {num_logs} messages in {duration:.2f}s")
    print(f"   Rate: {rate:.0f} messages/second")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*70)
    print("TRADINGAGENTS LOGGING SYSTEM TEST SUITE")
    print("="*70)
    
    tests = [
        test_basic_logging,
        test_session_tracking,
        test_helper_methods,
        test_error_logging,
        test_file_existence,
        test_log_rotation,
        test_colored_output,
        test_custom_config,
        test_environment_variables,
        test_performance
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {failed} test(s) failed")
    
    print("\nLog files location: ./logs/")
    print("  - tradingagents.log (all logs)")
    print("  - error.log (warnings and errors)")
    print("\nConfiguration file: config/logging.toml")
    print("="*70)


if __name__ == "__main__":
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Run all tests
    run_all_tests()

