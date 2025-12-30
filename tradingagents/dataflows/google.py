from typing import Annotated
from datetime import datetime
from dateutil.relativedelta import relativedelta
from .googlenews_utils import getNewsData


def get_google_news(
    ticker: Annotated[str, "Ticker symbol or query"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    """Get news for a specific ticker/query using Google News.
    
    This function adapts the standard (ticker, start_date, end_date) signature
    to work with Google News scraping.
    """
    # Use the ticker as the search query
    query = ticker.replace(" ", "+")
    
    # Google News expects the dates as strings in yyyy-mm-dd format
    news_results = getNewsData(query, start_date, end_date)

    news_str = ""

    for news in news_results:
        news_str += (
            f"### {news['title']} (source: {news['source']}) \n\n{news['snippet']}\n\n"
        )

    if len(news_results) == 0:
        return f"No news found for {ticker} from {start_date} to {end_date}"

    return f"## {ticker} Google News, from {start_date} to {end_date}:\n\n{news_str}"


def get_google_global_news(
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "Number of days to look back"] = 7,
    limit: Annotated[int, "Maximum number of articles to return"] = 5,
) -> str:
    """Get global/macroeconomic news using Google News."""
    # Search for general financial and economic news
    queries = [
        "global economy",
        "stock market",
        "federal reserve",
        "inflation",
        "interest rates",
    ]
    
    # Limit queries based on the limit parameter
    queries = queries[:min(limit, len(queries))]
    
    start_date = datetime.strptime(curr_date, "%Y-%m-%d")
    before = start_date - relativedelta(days=look_back_days)
    before_str = before.strftime("%Y-%m-%d")
    
    all_news = []
    seen_titles = set()
    
    for query in queries:
        query_formatted = query.replace(" ", "+")
        news_results = getNewsData(query_formatted, before_str, curr_date)
        
        # Deduplicate by title
        for news in news_results:
            if news['title'] not in seen_titles:
                seen_titles.add(news['title'])
                all_news.append(news)
                
                # Stop if we've reached the limit
                if len(all_news) >= limit:
                    break
        
        if len(all_news) >= limit:
            break
    
    if len(all_news) == 0:
        return ""
    
    news_str = ""
    for news in all_news[:limit]:
        news_str += (
            f"### {news['title']} (source: {news['source']}) \n\n{news['snippet']}\n\n"
        )
    
    return f"## Global News from {before_str} to {curr_date}:\n\n{news_str}"