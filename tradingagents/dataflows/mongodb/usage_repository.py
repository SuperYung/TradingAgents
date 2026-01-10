#!/usr/bin/env python3
"""
Usage Repository
CRUD operations for token_usage collection
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from tradingagents.config.mongodb_manager import get_mongodb_manager
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('agents')


class UsageRepository:
    """Repository for token usage tracking collection"""
    
    def __init__(self):
        self.manager = get_mongodb_manager()
        self.collection = None
        if self.manager.is_available():
            self.collection = self.manager.get_collection('token_usage')
            self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create indexes for optimal query performance"""
        if not self.collection:
            return
        
        try:
            # Query optimization indexes
            self.collection.create_index([("timestamp", -1)])
            self.collection.create_index([("analysis_id", 1)])
            self.collection.create_index([("symbol", 1), ("timestamp", -1)])
            self.collection.create_index([("provider", 1), ("model", 1), ("timestamp", -1)])
            
            logger.debug("✅ Usage repository indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    def log_usage(self, usage_data: Dict[str, Any]) -> bool:
        """
        Log LLM token usage
        
        Args:
            usage_data: Dictionary with usage information
            
        Returns:
            bool: Success status
        """
        if not self.collection:
            return False
        
        try:
            # Add timestamp if not present
            if 'timestamp' not in usage_data:
                usage_data['timestamp'] = datetime.utcnow()
            
            if 'created_at' not in usage_data:
                usage_data['created_at'] = datetime.utcnow()
            
            # Insert usage record
            self.collection.insert_one(usage_data)
            
            logger.debug(f"✅ Token usage logged: {usage_data.get('model', 'unknown')}")
            return True
                
        except Exception as e:
            logger.error(f"❌ Failed to log usage to MongoDB: {e}")
            return False
    
    def get_usage_by_analysis(self, analysis_id: str) -> List[Dict[str, Any]]:
        """Get all token usage for an analysis"""
        if not self.collection:
            return []
        
        try:
            cursor = self.collection.find(
                {"analysis_id": analysis_id},
                {"_id": 0}
            ).sort("timestamp", 1)
            
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to get usage for analysis {analysis_id}: {e}")
            return []
    
    def get_usage_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get usage within date range"""
        if not self.collection:
            return []
        
        try:
            cursor = self.collection.find(
                {
                    "timestamp": {
                        "$gte": datetime.fromisoformat(start_date),
                        "$lte": datetime.fromisoformat(end_date)
                    }
                },
                {"_id": 0}
            ).sort("timestamp", -1)
            
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to get usage by date range: {e}")
            return []
    
    def get_usage_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get usage summary for specified days
        
        Args:
            days: Number of days to look back
            
        Returns:
            Summary dictionary with totals and breakdowns
        """
        if not self.collection:
            return {"available": False}
        
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get all records in range
            cursor = self.collection.find(
                {"timestamp": {"$gte": start_date}},
                {"_id": 0}
            )
            
            records = list(cursor)
            
            if not records:
                return {
                    "available": True,
                    "days": days,
                    "total_records": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0
                }
            
            # Calculate totals
            total_tokens = sum(r.get('total_tokens', 0) for r in records)
            total_cost = sum(r.get('total_cost', 0.0) for r in records)
            
            # Break down by provider
            by_provider = {}
            for record in records:
                provider = record.get('provider', 'unknown')
                if provider not in by_provider:
                    by_provider[provider] = {
                        "count": 0,
                        "tokens": 0,
                        "cost": 0.0
                    }
                by_provider[provider]["count"] += 1
                by_provider[provider]["tokens"] += record.get('total_tokens', 0)
                by_provider[provider]["cost"] += record.get('total_cost', 0.0)
            
            # Break down by model
            by_model = {}
            for record in records:
                model = record.get('model', 'unknown')
                if model not in by_model:
                    by_model[model] = {
                        "count": 0,
                        "tokens": 0,
                        "cost": 0.0
                    }
                by_model[model]["count"] += 1
                by_model[model]["tokens"] += record.get('total_tokens', 0)
                by_model[model]["cost"] += record.get('total_cost', 0.0)
            
            return {
                "available": True,
                "days": days,
                "total_records": len(records),
                "total_tokens": total_tokens,
                "total_cost": round(total_cost, 2),
                "by_provider": by_provider,
                "by_model": by_model
            }
            
        except Exception as e:
            logger.error(f"Failed to get usage summary: {e}")
            return {"available": False, "error": str(e)}
    
    def delete_old_usage(self, days: int = 90) -> int:
        """Delete usage records older than specified days"""
        if not self.collection:
            return 0
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            result = self.collection.delete_many({"timestamp": {"$lt": cutoff_date}})
            
            if result.deleted_count > 0:
                logger.info(f"✅ Deleted {result.deleted_count} old usage records")
            
            return result.deleted_count
        except Exception as e:
            logger.error(f"Failed to delete old usage: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get repository statistics"""
        if not self.collection:
            return {"available": False}
        
        try:
            total_count = self.collection.count_documents({})
            
            # Get unique providers
            providers = self.collection.distinct("provider")
            
            # Get unique models
            models = self.collection.distinct("model")
            
            return {
                "available": True,
                "total_records": total_count,
                "unique_providers": len(providers),
                "unique_models": len(models),
                "providers": providers,
                "models": models[:10] if len(models) > 10 else models
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"available": False, "error": str(e)}

