#!/usr/bin/env python3
"""
Historical Data Repository
CRUD operations for historical_prices collection (OHLCV data)
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
from tradingagents.config.mongodb_manager import get_mongodb_manager
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('agents')


class HistoricalRepository:
    """Repository for historical price data collection"""
    
    def __init__(self):
        self.manager = get_mongodb_manager()
        self.collection = None
        if self.manager.is_available():
            self.collection = self.manager.get_collection('historical_prices')
            self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create indexes for optimal query performance"""
        if self.collection is None:
            return
        
        try:
            # Composite unique index
            self.collection.create_index([
                ("symbol", 1),
                ("trade_date", 1),
                ("period", 1),
                ("data_source", 1)
            ], unique=True)
            
            # Query optimization indexes
            self.collection.create_index([("symbol", 1), ("trade_date", -1)])
            self.collection.create_index([("symbol", 1)])
            self.collection.create_index([("trade_date", -1)])
            
            # TTL index for automatic cleanup
            self.collection.create_index([("ttl_expires", 1)], expireAfterSeconds=0)
            
            logger.debug("✅ Historical repository indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    def save_historical_data(self, symbol: str, data: pd.DataFrame, 
                           period: str = "1d", data_source: str = "yfinance",
                           ttl_days: int = 90) -> int:
        """
        Save historical OHLCV data to MongoDB
        
        Args:
            symbol: Stock symbol
            data: DataFrame with OHLCV data (index = dates)
            period: Time period (1d, 1wk, 1mo, etc.)
            data_source: Data provider name
            ttl_days: Days until automatic expiration
            
        Returns:
            int: Number of records saved
        """
        if self.collection is None or data.empty:
            return 0
        
        try:
            now = datetime.utcnow()
            ttl_expires = now + timedelta(days=ttl_days)
            saved_count = 0
            
            # Convert DataFrame to documents
            for date_index, row in data.iterrows():
                # Handle different date formats
                if isinstance(date_index, pd.Timestamp):
                    trade_date = date_index.strftime('%Y-%m-%d')
                else:
                    trade_date = str(date_index)
                
                document = {
                    "symbol": symbol.upper(),
                    "trade_date": trade_date,
                    "period": period,
                    "data_source": data_source,
                    
                    # OHLCV data
                    "open": float(row.get('Open', 0)) if pd.notna(row.get('Open')) else None,
                    "high": float(row.get('High', 0)) if pd.notna(row.get('High')) else None,
                    "low": float(row.get('Low', 0)) if pd.notna(row.get('Low')) else None,
                    "close": float(row.get('Close', 0)) if pd.notna(row.get('Close')) else None,
                    "volume": int(row.get('Volume', 0)) if pd.notna(row.get('Volume')) else None,
                    "adjusted_close": float(row.get('Adj Close', row.get('Close', 0))) if pd.notna(row.get('Adj Close', row.get('Close'))) else None,
                    
                    # Metadata
                    "created_at": now,
                    "updated_at": now,
                    "ttl_expires": ttl_expires
                }
                
                # Upsert
                result = self.collection.replace_one(
                    {
                        "symbol": symbol.upper(),
                        "trade_date": trade_date,
                        "period": period,
                        "data_source": data_source
                    },
                    document,
                    upsert=True
                )
                
                if result.upserted_id or result.modified_count > 0:
                    saved_count += 1
            
            if saved_count > 0:
                logger.info(f"✅ Saved {saved_count} historical records for {symbol} to MongoDB")
            
            return saved_count
            
        except Exception as e:
            logger.error(f"❌ Failed to save historical data to MongoDB: {e}")
            return 0
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str,
                          period: str = "1d") -> Optional[pd.DataFrame]:
        """
        Get historical OHLCV data from MongoDB
        
        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            period: Time period
            
        Returns:
            DataFrame with OHLCV data or None
        """
        if self.collection is None:
            return None
        
        try:
            cursor = self.collection.find(
                {
                    "symbol": symbol.upper(),
                    "period": period,
                    "trade_date": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                },
                {"_id": 0}
            ).sort("trade_date", 1)
            
            records = list(cursor)
            
            if not records:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(records)
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df.set_index('trade_date', inplace=True)
            
            # Rename columns to match yfinance format
            column_mapping = {
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'volume': 'Volume',
                'adjusted_close': 'Adj Close'
            }
            df.rename(columns=column_mapping, inplace=True)
            
            # Select only OHLCV columns
            ohlcv_columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close']
            df = df[[col for col in ohlcv_columns if col in df.columns]]
            
            logger.debug(f"✅ Retrieved {len(df)} historical records for {symbol} from MongoDB")
            return df
            
        except Exception as e:
            logger.error(f"Failed to get historical data from MongoDB: {e}")
            return None
    
    def delete_old_data(self, days: int = 90) -> int:
        """Delete data older than specified days"""
        if self.collection is None:
            return 0
        
        try:
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime('%Y-%m-%d')
            result = self.collection.delete_many({"trade_date": {"$lt": cutoff_date}})
            
            if result.deleted_count > 0:
                logger.info(f"✅ Deleted {result.deleted_count} old historical records")
            
            return result.deleted_count
        except Exception as e:
            logger.error(f"Failed to delete old data: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get repository statistics"""
        if self.collection is None:
            return {"available": False}
        
        try:
            total_count = self.collection.count_documents({})
            
            # Get unique symbols
            symbols = self.collection.distinct("symbol")
            
            return {
                "available": True,
                "total_records": total_count,
                "unique_symbols": len(symbols),
                "symbols_sample": symbols[:10] if len(symbols) > 10 else symbols
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"available": False, "error": str(e)}

