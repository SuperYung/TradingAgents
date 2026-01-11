"""
News MongoDB Integration
Intercepts news API calls and saves articles to MongoDB
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from tradingagents.utils.logging_manager import get_logger
from tradingagents.dataflows.mongodb.news_repository import NewsRepository
from tradingagents.default_config import DEFAULT_CONFIG

logger = get_logger('tradingagents.dataflows.news_saver')


class NewsSaver:
    """Saves news articles to MongoDB when fetched"""
    
    def __init__(self):
        self.enabled = (
            DEFAULT_CONFIG.get('mongodb_enabled', False) and 
            DEFAULT_CONFIG.get('mongodb_save_news', True)
        )
        if self.enabled:
            self.repo = NewsRepository()
            logger.info("📰 News saver initialized (MongoDB enabled)")
        else:
            self.repo = None
            logger.debug("📰 News saver disabled")
    
    def save_news_from_response(
        self, 
        news_data: Any, 
        symbol: Optional[str] = None,
        source: str = "unknown"
    ) -> int:
        """
        Extract and save news articles from API response
        
        Args:
            news_data: News data from API (dict, JSON string, or other format)
            symbol: Stock symbol (optional)
            source: Data source (alpha_vantage, openai, google, etc.)
            
        Returns:
            Number of articles saved
        """
        logger.info(f"📰 [NewsSaver] save_news_from_response called")
        logger.info(f"📰 [NewsSaver] enabled={self.enabled}, repo={self.repo is not None}, collection={self.repo.collection if self.repo else None}")
        
        if not self.enabled or self.repo is None or self.repo.collection is None:
            logger.warning(f"📰 [NewsSaver] Skipped - enabled={self.enabled}, repo={self.repo is not None}, collection={self.repo.collection if self.repo else None}")
            return 0
        
        try:
            logger.info(f"📰 [NewsSaver] Processing news_data type={type(news_data)}, symbol={symbol}, source={source}")
            
            # Parse news_data if it's a string
            if isinstance(news_data, str):
                logger.info(f"📰 [NewsSaver] Parsing JSON string...")
                try:
                    news_data = json.loads(news_data)
                    logger.info(f"📰 [NewsSaver] Parsed to dict with keys: {list(news_data.keys()) if isinstance(news_data, dict) else 'not a dict'}")
                except json.JSONDecodeError as e:
                    logger.warning(f"📰 [NewsSaver] JSON parse error: {e}")
                    return 0
            
            if not isinstance(news_data, dict):
                logger.warning(f"📰 [NewsSaver] News data is {type(news_data)}, not dict. Skipping.")
                return 0
            
            logger.info(f"📰 [NewsSaver] News data keys: {list(news_data.keys())}")
            
            # Extract articles based on source format
            articles = self._extract_articles(news_data, symbol, source)
            logger.info(f"📰 [NewsSaver] Extracted {len(articles)} articles")
            
            if not articles:
                logger.warning("📰 [NewsSaver] No articles extracted from news data")
                return 0
            
            # Save articles
            logger.info(f"📰 Saving {len(articles)} news articles to MongoDB...")
            saved_count = self.repo.save_news_batch(articles, ttl_days=30)
            logger.info(f"✅ Saved {saved_count}/{len(articles)} news articles to MongoDB")
            
            return saved_count
            
        except Exception as e:
            logger.error(f"❌ Error saving news to MongoDB: {type(e).__name__}: {e}")
            return 0
    
    def _extract_articles(
        self, 
        news_data: Dict, 
        symbol: Optional[str],
        source: str
    ) -> List[Dict[str, Any]]:
        """Extract article list from different API response formats"""
        
        articles = []
        
        # Alpha Vantage NEWS_SENTIMENT format
        if 'feed' in news_data:
            for item in news_data.get('feed', []):
                article = self._parse_alpha_vantage_article(item, symbol, source)
                if article:
                    articles.append(article)
        
        # OpenAI/Generic format (list of articles)
        elif isinstance(news_data, list):
            for item in news_data:
                article = self._parse_generic_article(item, symbol, source)
                if article:
                    articles.append(article)
        
        # Generic dict with articles key
        elif 'articles' in news_data:
            for item in news_data.get('articles', []):
                article = self._parse_generic_article(item, symbol, source)
                if article:
                    articles.append(article)
        
        return articles
    
    def _parse_alpha_vantage_article(
        self, 
        item: Dict, 
        symbol: Optional[str],
        source: str
    ) -> Optional[Dict[str, Any]]:
        """Parse Alpha Vantage NEWS_SENTIMENT article format"""
        try:
            # Extract ticker sentiments
            ticker_sentiment = []
            related_symbols = []
            
            for ticker_data in item.get('ticker_sentiment', []):
                ticker_symbol = ticker_data.get('ticker')
                if ticker_symbol:
                    related_symbols.append(ticker_symbol)
                    ticker_sentiment.append({
                        'ticker': ticker_symbol,
                        'relevance': float(ticker_data.get('relevance_score', 0)),
                        'sentiment': ticker_data.get('ticker_sentiment_label', 'Neutral'),
                        'sentiment_score': float(ticker_data.get('ticker_sentiment_score', 0))
                    })
            
            # Build article document
            article = {
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'published_at': self._parse_datetime(item.get('time_published')),
                'source': {
                    'name': item.get('source', source),
                    'domain': item.get('source_domain', ''),
                    'api_source': 'alpha_vantage'
                },
                'summary': item.get('summary', ''),
                'topics': [topic.get('topic') for topic in item.get('topics', []) if topic.get('topic')],
                'symbols': list(set(related_symbols + ([symbol] if symbol else []))),
                'sentiment': {
                    'overall': item.get('overall_sentiment_label', 'Neutral'),
                    'score': float(item.get('overall_sentiment_score', 0)),
                    'tickers': ticker_sentiment
                },
                'authors': item.get('authors', []),
                'category': item.get('category_within_source', ''),
                'retrieved_at': datetime.utcnow()
            }
            
            return article
            
        except Exception as e:
            logger.debug(f"Error parsing Alpha Vantage article: {e}")
            return None
    
    def _parse_generic_article(
        self, 
        item: Dict, 
        symbol: Optional[str],
        source: str
    ) -> Optional[Dict[str, Any]]:
        """Parse generic article format"""
        try:
            article = {
                'title': item.get('title', ''),
                'url': item.get('url', item.get('link', '')),
                'published_at': self._parse_datetime(
                    item.get('published_at') or 
                    item.get('publishedAt') or 
                    item.get('date')
                ),
                'source': {
                    'name': item.get('source', {}).get('name', source) if isinstance(item.get('source'), dict) else item.get('source', source),
                    'api_source': source
                },
                'summary': item.get('summary', item.get('description', '')),
                'topics': item.get('topics', item.get('categories', [])),
                'symbols': ([symbol] if symbol else []) + item.get('symbols', []),
                'authors': item.get('authors', []),
                'retrieved_at': datetime.utcnow()
            }
            
            return article
            
        except Exception as e:
            logger.debug(f"Error parsing generic article: {e}")
            return None
    
    def _parse_datetime(self, dt_string: Optional[str]) -> Optional[datetime]:
        """Parse various datetime formats"""
        if not dt_string:
            return None
        
        try:
            # Try ISO format first
            return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        except:
            pass
        
        try:
            # Try Alpha Vantage format: 20240115T123000
            return datetime.strptime(dt_string, '%Y%m%dT%H%M%S')
        except:
            pass
        
        try:
            # Try common formats
            return datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
        except:
            pass
        
        logger.debug(f"Could not parse datetime: {dt_string}")
        return None


# Global instance
_news_saver = None

def get_news_saver() -> NewsSaver:
    """Get or create global NewsSaver instance"""
    global _news_saver
    if _news_saver is None:
        _news_saver = NewsSaver()
    return _news_saver

