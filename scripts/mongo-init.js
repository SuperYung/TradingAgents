// MongoDB Initialization Script for TradingAgents
// This script sets up collections and indexes

print('🚀 Initializing TradingAgents MongoDB database...');

// Switch to tradingagents database
db = db.getSiblingDB('tradingagents');

print('📊 Creating collections and indexes...');

// 1. Analysis Reports Collection
print('  Creating analysis_reports collection...');
db.createCollection('analysis_reports');
db.analysis_reports.createIndex({ "analysis_id": 1 }, { unique: true });
db.analysis_reports.createIndex({ "symbol": 1, "timestamp": -1 });
db.analysis_reports.createIndex({ "analysis_date": -1 });
db.analysis_reports.createIndex({ "status": 1 });
db.analysis_reports.createIndex({ "decision.action": 1 });
print('  ✅ analysis_reports indexes created');

// 2. Historical Prices Collection
print('  Creating historical_prices collection...');
db.createCollection('historical_prices');
db.historical_prices.createIndex(
    { "symbol": 1, "trade_date": 1, "period": 1, "data_source": 1 },
    { unique: true }
);
db.historical_prices.createIndex({ "symbol": 1, "trade_date": -1 });
db.historical_prices.createIndex({ "symbol": 1 });
db.historical_prices.createIndex({ "trade_date": -1 });
db.historical_prices.createIndex({ "ttl_expires": 1 }, { expireAfterSeconds: 0 });
print('  ✅ historical_prices indexes created');

// 3. News Articles Collection
print('  Creating news_articles collection...');
db.createCollection('news_articles');
db.news_articles.createIndex({ "article_id": 1 }, { unique: true });
db.news_articles.createIndex({ "symbol": 1, "published_at": -1 });
db.news_articles.createIndex({ "published_at": -1 });
db.news_articles.createIndex({ "topics": 1 });
db.news_articles.createIndex({ "ttl_expires": 1 }, { expireAfterSeconds: 0 });
print('  ✅ news_articles indexes created');

// 4. Token Usage Collection
print('  Creating token_usage collection...');
db.createCollection('token_usage');
db.token_usage.createIndex({ "timestamp": -1 });
db.token_usage.createIndex({ "analysis_id": 1 });
db.token_usage.createIndex({ "symbol": 1, "timestamp": -1 });
db.token_usage.createIndex({ "provider": 1, "model": 1, "timestamp": -1 });
print('  ✅ token_usage indexes created');

// Insert sample configuration document
print('  Creating metadata collection...');
db.createCollection('_metadata');
db._metadata.insertOne({
    "initialized_at": new Date(),
    "version": "1.0.0",
    "collections": [
        "analysis_reports",
        "historical_prices",
        "news_articles",
        "token_usage"
    ],
    "description": "TradingAgents MongoDB database"
});
print('  ✅ metadata created');

// Display collection stats
print('\n📈 Collection Statistics:');
print('  analysis_reports:', db.analysis_reports.countDocuments({}), 'documents');
print('  historical_prices:', db.historical_prices.countDocuments({}), 'documents');
print('  news_articles:', db.news_articles.countDocuments({}), 'documents');
print('  token_usage:', db.token_usage.countDocuments({}), 'documents');

print('\n✅ MongoDB initialization complete!');
print('📊 Database: tradingagents');
print('🔗 Connection: mongodb://localhost:27017/tradingagents');

