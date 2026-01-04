from typing import Annotated
from datetime import datetime
from dateutil.relativedelta import relativedelta
from .googlenews_utils import getNewsData


def get_google_news(
    query: Annotated[str, "Query to search with"],
    curr_date: Annotated[str, "Curr date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
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

def get_global_news_google(
    curr_date: str,
    look_back_days: int = 7,
    limit: int = 5,
) -> str:
    """Get global macroeconomic news using Google News"""
    # Use generic macroeconomic search terms
    queries = [
        "economy",
        "federal reserve",
        "stock market",
        "inflation",
        "interest rates"
    ]
    
    all_news = []
    for query in queries:
        news = get_google_news(query, curr_date, look_back_days)
        if news:
            all_news.append(news)
    
    if not all_news:
        return "No global news found"
    
    return "\n\n---\n\n".join(all_news[:limit])    