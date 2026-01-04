from langchain_core.tools import tool
from typing import Annotated, Dict, Any, Optional
import asyncio
from tradingagents.dataflows.data_source_manager import DataSourceManager
from tradingagents.utils.logging_manager import get_logger

logger = get_logger("tradingagents.agents.fundamental_data_tools")

# Initialize DataSourceManager (singleton)
_data_manager = None

def get_data_manager() -> DataSourceManager:
    """Get or create DataSourceManager instance."""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataSourceManager()
    return _data_manager


def format_fundamentals_report(data: Dict[str, Any], ticker: str) -> str:
    """Format fundamental data into a readable report."""
    if not data:
        return f"No fundamental data available for {ticker}"
    
    report_lines = [
        f"=== Fundamental Analysis Report for {ticker} ===",
        f"Data Source: {data.get('provider', 'Unknown')}",
        "",
        "Key Metrics:",
        f"  • P/E Ratio: {data.get('pe_ratio', 'N/A')}",
        f"  • EPS: {data.get('eps', 'N/A')}",
        f"  • Dividend Yield: {data.get('dividend_yield', 'N/A')}",
        f"  • Beta: {data.get('beta', 'N/A')}",
        "",
        "Valuation:",
        f"  • 52-Week High: ${data.get('52_week_high', 'N/A')}",
        f"  • 52-Week Low: ${data.get('52_week_low', 'N/A')}",
        f"  • Price-to-Book: {data.get('price_to_book', 'N/A')}",
        "",
        "Performance:",
        f"  • Profit Margin: {data.get('profit_margin', 'N/A')}",
        f"  • Revenue: ${data.get('revenue', 'N/A')}",
        f"  • Earnings Growth: {data.get('earnings_growth', 'N/A')}",
    ]
    
    return "\n".join(report_lines)


@tool
def get_fundamentals(
    ticker: Annotated[str, "ticker symbol"],
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
) -> str:
    """
    Retrieve comprehensive fundamental data for a given ticker symbol.
    Uses multi-source data providers with automatic fallback.
    Args:
        ticker (str): Ticker symbol of the company
        curr_date (str): Current date you are trading at, yyyy-mm-dd
    Returns:
        str: A formatted report containing comprehensive fundamental data
    """
    try:
        manager = get_data_manager()
        # Run async call in sync context
        data = asyncio.run(manager.get_fundamentals(ticker))
        
        if not data:
            return f"Unable to retrieve fundamental data for {ticker}. Please check the symbol and try again."
        
        return format_fundamentals_report(data, ticker)
    except Exception as e:
        logger.error(f"Error getting fundamentals for {ticker}: {e}")
        return f"Error retrieving fundamental data for {ticker}: {str(e)}"


@tool
def get_balance_sheet(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[str, "reporting frequency: annual/quarterly"] = "quarterly",
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"] = None,
) -> str:
    """
    Retrieve balance sheet data for a given ticker symbol.
    Uses yfinance data provider.
    Args:
        ticker (str): Ticker symbol of the company
        freq (str): Reporting frequency: annual/quarterly (default quarterly)
        curr_date (str): Current date you are trading at, yyyy-mm-dd
    Returns:
        str: A formatted report containing balance sheet data
    """
    try:
        from tradingagents.dataflows.y_finance import get_balance_sheet as yf_get_balance_sheet
        return yf_get_balance_sheet(ticker, freq, curr_date)
    except Exception as e:
        logger.error(f"Error getting balance sheet for {ticker}: {e}")
        return f"Error retrieving balance sheet for {ticker}: {str(e)}"


@tool
def get_cashflow(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[str, "reporting frequency: annual/quarterly"] = "quarterly",
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"] = None,
) -> str:
    """
    Retrieve cash flow statement data for a given ticker symbol.
    Uses yfinance data provider.
    Args:
        ticker (str): Ticker symbol of the company
        freq (str): Reporting frequency: annual/quarterly (default quarterly)
        curr_date (str): Current date you are trading at, yyyy-mm-dd
    Returns:
        str: A formatted report containing cash flow statement data
    """
    try:
        from tradingagents.dataflows.y_finance import get_cashflow as yf_get_cashflow
        return yf_get_cashflow(ticker, freq, curr_date)
    except Exception as e:
        logger.error(f"Error getting cashflow for {ticker}: {e}")
        return f"Error retrieving cashflow for {ticker}: {str(e)}"


@tool
def get_income_statement(
    ticker: Annotated[str, "ticker symbol"],
    freq: Annotated[str, "reporting frequency: annual/quarterly"] = "quarterly",
    curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"] = None,
) -> str:
    """
    Retrieve income statement data for a given ticker symbol.
    Uses yfinance data provider.
    Args:
        ticker (str): Ticker symbol of the company
        freq (str): Reporting frequency: annual/quarterly (default quarterly)
        curr_date (str): Current date you are trading at, yyyy-mm-dd
    Returns:
        str: A formatted report containing income statement data
    """
    try:
        from tradingagents.dataflows.y_finance import get_income_statement as yf_get_income_statement
        return yf_get_income_statement(ticker, freq, curr_date)
    except Exception as e:
        logger.error(f"Error getting income statement for {ticker}: {e}")
        return f"Error retrieving income statement for {ticker}: {str(e)}"