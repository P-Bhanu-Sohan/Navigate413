import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorGridFSBucket
from pymongo import ASCENDING, DESCENDING
from config import MONGODB_URI, MONGODB_DB_NAME

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient = None
_db: AsyncIOMotorDatabase = None
_gridfs_bucket: AsyncIOMotorGridFSBucket = None


async def connect_to_mongo():
    """Initialize MongoDB connection."""
    global _client, _db, _gridfs_bucket
    try:
        _client = AsyncIOMotorClient(MONGODB_URI)
        _db = _client[MONGODB_DB_NAME]
        
        # Initialize GridFS bucket for PDF storage
        _gridfs_bucket = AsyncIOMotorGridFSBucket(_db)
        
        # Verify connection
        await _db.command("ping")
        logger.info("Connected to MongoDB Atlas")
        
        # Create indexes
        await _create_indexes()
        return _db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def disconnect_from_mongo():
    """Close MongoDB connection."""
    global _client
    if _client:
        _client.close()
        logger.info("Disconnected from MongoDB Atlas")


async def _create_indexes():
    """Create necessary MongoDB indexes."""
    if _db is None:
        return
    
    try:
        # Documents metadata collection indexes
        docs_col = _db["documents_metadata"]
        await docs_col.create_index([("user_session_id", ASCENDING)])
        await docs_col.create_index([("upload_timestamp", DESCENDING)])
        
        # campus_embeddings collection indexes
        embeddings_col = _db["campus_embeddings"]
        await embeddings_col.create_index([("session_id", ASCENDING)])
        await embeddings_col.create_index([("domain", ASCENDING)])
        
        logger.info("MongoDB indexes created successfully")
    except Exception as e:
        logger.warning(f"Index creation warning (may already exist): {e}")


def get_db() -> AsyncIOMotorDatabase:
    """Get the current database instance."""
    if _db is None:
        raise RuntimeError("Database not connected. Call connect_to_mongo() first.")
    return _db


def get_gridfs_bucket() -> AsyncIOMotorGridFSBucket:
    """Get the GridFS bucket for file storage."""
    if _gridfs_bucket is None:
        raise RuntimeError("GridFS bucket not initialized. Call connect_to_mongo() first.")
    return _gridfs_bucket
