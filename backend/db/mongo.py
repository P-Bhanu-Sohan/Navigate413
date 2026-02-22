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
        logger.info(f"[MONGO_CONNECT] Attempting to connect to MongoDB Atlas...")
        logger.info(f"[MONGO_CONNECT] Database name: {MONGODB_DB_NAME}")
        _client = AsyncIOMotorClient(MONGODB_URI)
        _db = _client[MONGODB_DB_NAME]
        logger.info(f"[MONGO_CONNECT] Client created successfully")
        
        # Initialize GridFS bucket for PDF storage
        _gridfs_bucket = AsyncIOMotorGridFSBucket(_db)
        logger.info(f"[MONGO_CONNECT] GridFS bucket initialized")
        
        # Verify connection
        logger.info(f"[MONGO_CONNECT] Pinging database to verify connection...")
        await _db.command("ping")
        logger.info("[MONGO_CONNECT] ✓ Connected to MongoDB Atlas successfully")
        
        # Create indexes
        logger.info(f"[MONGO_CONNECT] Creating indexes...")
        await _create_indexes()
        return _db
    except Exception as e:
        logger.error(f"[MONGO_CONNECT] FAILED: {e}", exc_info=True)
        raise


async def disconnect_from_mongo():
    """Close MongoDB connection."""
    global _client
    if _client:
        logger.info(f"[MONGO_DISCONNECT] Closing MongoDB connection...")
        _client.close()
        logger.info("[MONGO_DISCONNECT] ✓ Disconnected from MongoDB Atlas")


async def _create_indexes():
    """Create necessary MongoDB indexes."""
    if _db is None:
        logger.warning("[CREATE_INDEXES] Database not initialized, skipping index creation")
        return
    
    try:
        logger.info(f"[CREATE_INDEXES] Starting index creation...")
        
        # Documents metadata collection indexes
        logger.info(f"[CREATE_INDEXES] Creating indexes for documents_metadata collection...")
        docs_col = _db["documents_metadata"]
        await docs_col.create_index([("user_session_id", ASCENDING)])
        logger.info(f"[CREATE_INDEXES] ✓ Created index on user_session_id")
        await docs_col.create_index([("upload_timestamp", DESCENDING)])
        logger.info(f"[CREATE_INDEXES] ✓ Created index on upload_timestamp")
        
        # Embeddings collection indexes (renamed from clause_embeddings)
        logger.info(f"[CREATE_INDEXES] Creating indexes for Embeddings collection...")
        embeddings_col = _db["Embeddings"]
        await embeddings_col.create_index([("session_id", ASCENDING)])
        logger.info(f"[CREATE_INDEXES] ✓ Created index on session_id")
        await embeddings_col.create_index([("domain", ASCENDING)])
        logger.info(f"[CREATE_INDEXES] ✓ Created index on domain")
        
        logger.info("[CREATE_INDEXES] ✓ All MongoDB indexes created successfully")
    except Exception as e:
        logger.warning(f"[CREATE_INDEXES] Warning (indexes may already exist): {e}")


def get_db() -> AsyncIOMotorDatabase:
    """Get the current database instance."""
    if _db is None:
        logger.error("[GET_DB] Database not connected!")
        raise RuntimeError("Database not connected. Call connect_to_mongo() first.")
    logger.debug(f"[GET_DB] Returning database instance: {MONGODB_DB_NAME}")
    return _db


def get_gridfs_bucket() -> AsyncIOMotorGridFSBucket:
    """Get the GridFS bucket for file storage."""
    if _gridfs_bucket is None:
        logger.error("[GET_GRIDFS] GridFS bucket not initialized!")
        raise RuntimeError("GridFS bucket not initialized. Call connect_to_mongo() first.")
    logger.debug(f"[GET_GRIDFS] Returning GridFS bucket")
    return _gridfs_bucket
