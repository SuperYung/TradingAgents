from typing import Annotated
from datetime import datetime
from dateutil.relativedelta import relativedelta
from .googlenews_utils import getNewsData


def get_google_news(
    query: Annotated[str, "Query to search with"],
    curr_date: Annotated[str, "Curr date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    """Get news for a specific query using Google News."""
    query = query.replace(" ", "+")

    start_date = datetime.strptime(curr_date, "%Y-%m-%d")
    before = start_date - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    news_results = getNewsData(query, before, curr_date)

    news_str = ""

    for news in news_results:
        news_str += (
            f"### {news['title']} (source: {news['source']}) \n\n{news['snippet']}\n\n"
        )

    if len(news_results) == 0:
        return ""

    return f"## {query} Google News, from {before} to {curr_date}:\n\n{news_str}"


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