#!/usr/bin/env python3
"""
MongoDB Connection Manager
Provides centralized MongoDB connection management with health checks and graceful fallback
"""

import os
from typing import Optional
from pathlib import Path

# Import logging
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')

# Try to import MongoDB drivers
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    MongoClient = None
    logger.debug("pymongo not installed - MongoDB features disabled")

# Try to import async MongoDB driver
try:
    from motor.motor_asyncio import AsyncIOMotorClient
    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False
    AsyncIOMotorClient = None
    logger.debug("motor not installed - Async MongoDB features disabled")

# Load environment variables
try:
    from dotenv import load_dotenv
    # Load .env from project root
    project_root = Path(__file__).parent.parent.parent
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        logger.debug(f"Loaded .env from {env_path}")
except ImportError:
    logger.debug("python-dotenv not installed - using system environment only")


class MongoDBManager:
    """MongoDB connection manager with health checks and connection pooling"""
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.db = None
        self.available = False
        self.enabled = os.getenv('MONGODB_ENABLED', 'false').lower() == 'true'
        
        if not PYMONGO_AVAILABLE:
            logger.info("📦 MongoDB disabled: pymongo not installed")
            logger.info("   Install with: pip install pymongo")
            return
        
        if not self.enabled:
            logger.info("📦 MongoDB disabled via MONGODB_ENABLED=false")
            return
        
        # Get MongoDB configuration from environment
        self.host = os.getenv('MONGODB_HOST', 'localhost')
        self.port = int(os.getenv('MONGODB_PORT', '27017'))
        self.database = os.getenv('MONGODB_DATABASE', 'tradingagents')
        self.username = os.getenv('MONGODB_USERNAME', '')
        self.password = os.getenv('MONGODB_PASSWORD', '')
        self.auth_source = os.getenv('MONGODB_AUTH_SOURCE', 'admin')
        
        # Connection pool settings
        self.max_pool_size = int(os.getenv('MONGO_MAX_CONNECTIONS', '50'))
        self.min_pool_size = int(os.getenv('MONGO_MIN_CONNECTIONS', '5'))
        
        # Timeout settings (milliseconds)
        self.connect_timeout = int(os.getenv('MONGO_CONNECT_TIMEOUT_MS', '10000'))
        self.socket_timeout = int(os.getenv('MONGO_SOCKET_TIMEOUT_MS', '20000'))
        self.server_selection_timeout = int(os.getenv('MONGO_SERVER_SELECTION_TIMEOUT_MS', '5000'))
        
        # Initialize connection
        self._connect()
    
    def _connect(self):
        """Establish MongoDB connection with configured settings"""
        try:
            # Build connection string
            if self.username and self.password:
                connection_string = (
                    f"mongodb://{self.username}:{self.password}@"
                    f"{self.host}:{self.port}/{self.database}?"
                    f"authSource={self.auth_source}"
                )
            else:
                connection_string = f"mongodb://{self.host}:{self.port}/{self.database}"
            
            # Create client with connection pool settings
            self.client = MongoClient(
                connection_string,
                maxPoolSize=self.max_pool_size,
                minPoolSize=self.min_pool_size,
                serverSelectionTimeoutMS=self.server_selection_timeout,
                connectTimeoutMS=self.connect_timeout,
                socketTimeoutMS=self.socket_timeout
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            # Get database
            self.db = self.client[self.database]
            
            self.available = True
            logger.info("✅ MongoDB connected successfully")
            logger.info(f"   📊 Database: {self.database}")
            logger.info(f"   🔗 Host: {self.host}:{self.port}")
            logger.info(f"   🏊 Pool: {self.min_pool_size}-{self.max_pool_size} connections")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.warning(f"⚠️  MongoDB connection failed: {e}")
            logger.info("   Will use Redis + File cache fallback")
            self.available = False
            self.client = None
            self.db = None
        except Exception as e:
            logger.error(f"❌ MongoDB initialization error: {e}")
            self.available = False
            self.client = None
            self.db = None
    
    def get_collection(self, collection_name: str):
        """Get a MongoDB collection"""
        if not self.available or not self.db:
            return None
        return self.db[collection_name]
    
    def is_available(self) -> bool:
        """Check if MongoDB is available"""
        return self.available and self.client is not None
    
    def health_check(self) -> bool:
        """Perform health check on MongoDB connection"""
        if not self.is_available():
            return False
        
        try:
            self.client.admin.command('ping')
            return True
        except Exception as e:
            logger.warning(f"MongoDB health check failed: {e}")
            self.available = False
            return False
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
            self.available = False


# Global MongoDB manager instance
_mongodb_manager = None


def get_mongodb_manager() -> MongoDBManager:
    """Get global MongoDB manager instance"""
    global _mongodb_manager
    if _mongodb_manager is None:
        _mongodb_manager = MongoDBManager()
    return _mongodb_manager


def get_mongodb_client():
    """Get MongoDB client (backward compatibility)"""
    manager = get_mongodb_manager()
    return manager.client if manager.is_available() else None


def get_mongodb_database():
    """Get MongoDB database"""
    manager = get_mongodb_manager()
    return manager.db if manager.is_available() else None

