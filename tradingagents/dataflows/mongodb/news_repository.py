#!/usr/bin/env python3
"""
News Repository
CRUD operations for news_articles collection
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from tradingagents.config.mongodb_manager import get_mongodb_manager
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('agents')


class NewsRepository:
    """Repository for news articles collection"""
    
    def __init__(self):
        self.manager = get_mongodb_manager()
        self.collection = None
        if self.manager.is_available():
            self.collection = self.manager.get_collection('news_articles')
            self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create indexes for optimal query performance"""
        if self.collection is None:
            return
        
        try:
            # Unique index on article_id
            self.collection.create_index("article_id", unique=True)
            
            # Query optimization indexes
            self.collection.create_index([("symbol", 1), ("published_at", -1)])
            self.collection.create_index([("published_at", -1)])
            self.collection.create_index([("topics", 1)])
            
            # TTL index for automatic cleanup
            self.collection.create_index([("ttl_expires", 1)], expireAfterSeconds=0)
            
            logger.debug("✅ News repository indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    def save_news_article(self, article: Dict[str, Any], ttl_days: int = 30) -> bool:
        """
        Save news article to MongoDB
        
        Args:
            article: News article dictionary
            ttl_days: Days until automatic expiration
            
        Returns:
            bool: Success status
        """
        if self.collection is None:
            return False
        
        try:
            # Ensure required fields
            if 'article_id' not in article:
                # Generate article_id from URL or title hash
                import hashlib
                article_id = hashlib.md5(
                    article.get('url', article.get('title', '')).encode()
                ).hexdigest()
                article['article_id'] = article_id
            
            # Add timestamps
            now = datetime.utcnow()
            if 'created_at' not in article:
                article['created_at'] = now
            article['updated_at'] = now
            article['ttl_expires'] = now + timedelta(days=ttl_days)
            
            # Upsert
            result = self.collection.replace_one(
                {"article_id": article['article_id']},
                article,
                upsert=True
            )
            
            if result.upserted_id or result.modified_count > 0:
                logger.debug(f"✅ News article saved to MongoDB: {article.get('title', '')[:50]}")
                return True
            return True
                
        except Exception as e:
            logger.error(f"❌ Failed to save news article to MongoDB: {e}")
            return False
    
    def save_news_batch(self, articles: List[Dict[str, Any]], ttl_days: int = 30) -> int:
        """Save multiple news articles"""
        if self.collection is None or not articles:
            return 0
        
        saved_count = 0
        for article in articles:
            if self.save_news_article(article, ttl_days):
                saved_count += 1
        
        if saved_count > 0:
            logger.info(f"✅ Saved {saved_count} news articles to MongoDB")
        
        return saved_count
    
    def get_news_by_symbol(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent news for a symbol"""
        if self.collection is None:
            return []
        
        try:
            cursor = self.collection.find(
                {"symbol": symbol.upper()},
                {"_id": 0}
            ).sort("published_at", -1).limit(limit)
            
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to get news for {symbol}: {e}")
            return []
    
    def get_news_by_date_range(self, start_date: str, end_date: str, 
                               symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get news within date range"""
        if self.collection is None:
            return []
        
        try:
            query = {
                "published_at": {
                    "$gte": datetime.fromisoformat(start_date),
                    "$lte": datetime.fromisoformat(end_date)
                }
            }
            
            if symbol:
                query["symbol"] = symbol.upper()
            
            cursor = self.collection.find(
                query,
                {"_id": 0}
            ).sort("published_at", -1)
            
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to get news by date range: {e}")
            return []
    
    def get_news_by_topics(self, topics: List[str], limit: int = 20) -> List[Dict[str, Any]]:
        """Get news by topics/tags"""
        if self.collection is None:
            return []
        
        try:
            cursor = self.collection.find(
                {"topics": {"$in": topics}},
                {"_id": 0}
            ).sort("published_at", -1).limit(limit)
            
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to get news by topics: {e}")
            return []
    
    def delete_old_news(self, days: int = 30) -> int:
        """Delete news older than specified days"""
        if self.collection is None:
            return 0
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            result = self.collection.delete_many({"published_at": {"$lt": cutoff_date}})
            
            if result.deleted_count > 0:
                logger.info(f"✅ Deleted {result.deleted_count} old news articles")
            
            return result.deleted_count
        except Exception as e:
            logger.error(f"Failed to delete old news: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get repository statistics"""
        if self.collection is None:
            return {"available": False}
        
        try:
            total_count = self.collection.count_documents({})
            
            # Get unique symbols
            symbols = self.collection.distinct("symbol")
            
            # Get recent count (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_count = self.collection.count_documents({"published_at": {"$gte": week_ago}})
            
            return {
                "available": True,
                "total_articles": total_count,
                "unique_symbols": len(symbols),
                "recent_7days": recent_count
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"available": False, "error": str(e)}

