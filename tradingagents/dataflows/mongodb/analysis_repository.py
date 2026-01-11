#!/usr/bin/env python3
"""
Analysis Repository
CRUD operations for analysis_reports collection
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from tradingagents.config.mongodb_manager import get_mongodb_manager
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('agents')


class AnalysisRepository:
    """Repository for analysis reports collection"""
    
    def __init__(self):
        self.manager = get_mongodb_manager()
        self.collection = None
        if self.manager.is_available():
            self.collection = self.manager.get_collection('analysis_reports')
            self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create indexes for optimal query performance"""
        if self.collection is None:
            return
        
        try:
            # Unique index on analysis_id
            self.collection.create_index("analysis_id", unique=True)
            
            # Query optimization indexes
            self.collection.create_index([("symbol", 1), ("timestamp", -1)])
            self.collection.create_index([("analysis_date", -1)])
            self.collection.create_index([("status", 1)])
            self.collection.create_index([("decision.action", 1)])
            
            logger.debug("✅ Analysis repository indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    def save_analysis(self, analysis_data: Dict[str, Any]) -> bool:
        """
        Save analysis result to MongoDB
        
        Args:
            analysis_data: Complete analysis result dictionary
            
        Returns:
            bool: Success status
        """
        if self.collection is None:
            logger.debug("MongoDB not available, skipping analysis save")
            return False
        
        try:
            # Ensure required fields
            if 'analysis_id' not in analysis_data:
                logger.error("Missing analysis_id in analysis data")
                return False
            
            # Add timestamps
            now = datetime.utcnow()
            if 'created_at' not in analysis_data:
                analysis_data['created_at'] = now
            analysis_data['updated_at'] = now
            
            # Upsert (insert or update)
            result = self.collection.replace_one(
                {"analysis_id": analysis_data['analysis_id']},
                analysis_data,
                upsert=True
            )
            
            if result.upserted_id or result.modified_count > 0:
                logger.info(f"✅ Analysis saved to MongoDB: {analysis_data['analysis_id']}")
                return True
            else:
                logger.warning(f"⚠️  No changes made for: {analysis_data['analysis_id']}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to save analysis to MongoDB: {e}")
            return False
    
    def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis by analysis_id"""
        if self.collection is None:
            return None
        
        try:
            result = self.collection.find_one(
                {"analysis_id": analysis_id},
                {"_id": 0}
            )
            return result
        except Exception as e:
            logger.error(f"Failed to get analysis {analysis_id}: {e}")
            return None
    
    def get_analyses_by_symbol(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent analyses for a symbol"""
        if self.collection is None:
            return []
        
        try:
            cursor = self.collection.find(
                {"symbol": symbol},
                {"_id": 0}
            ).sort("timestamp", -1).limit(limit)
            
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to get analyses for {symbol}: {e}")
            return []
    
    def get_recent_analyses(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get most recent analyses"""
        if self.collection is None:
            return []
        
        try:
            cursor = self.collection.find(
                {},
                {"_id": 0}
            ).sort("timestamp", -1).limit(limit)
            
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to get recent analyses: {e}")
            return []
    
    def get_analyses_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get analyses within date range"""
        if self.collection is None:
            return []
        
        try:
            cursor = self.collection.find(
                {
                    "analysis_date": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                },
                {"_id": 0}
            ).sort("analysis_date", -1)
            
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to get analyses by date range: {e}")
            return []
    
    def delete_analysis(self, analysis_id: str) -> bool:
        """Delete an analysis"""
        if self.collection is None:
            return False
        
        try:
            result = self.collection.delete_one({"analysis_id": analysis_id})
            if result.deleted_count > 0:
                logger.info(f"✅ Deleted analysis: {analysis_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete analysis {analysis_id}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get repository statistics"""
        if self.collection is None:
            return {"available": False}
        
        try:
            total_count = self.collection.count_documents({})
            
            # Get counts by status
            status_counts = {}
            for status in ['completed', 'failed', 'pending']:
                count = self.collection.count_documents({"status": status})
                if count > 0:
                    status_counts[status] = count
            
            # Get counts by decision action
            action_counts = {}
            for action in ['BUY', 'SELL', 'HOLD']:
                count = self.collection.count_documents({"decision.action": action})
                if count > 0:
                    action_counts[action] = count
            
            return {
                "available": True,
                "total_analyses": total_count,
                "by_status": status_counts,
                "by_action": action_counts
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"available": False, "error": str(e)}

