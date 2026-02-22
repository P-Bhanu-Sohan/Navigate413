import logging
from typing import Optional, List, Dict, Any
import google.generativeai as genai
from config import GEMINI_EMBEDDING_MODEL, GEMINI_API_KEY
from db.mongo import get_db

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


async def embed_text(text: str) -> List[float]:
    """Generate embedding for text using Gemini."""
    try:
        logger.info(f"[EMBED_TEXT] Calling Gemini API with model: {GEMINI_EMBEDDING_MODEL}")
        result = genai.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            content=text
        )
        logger.info(f"[EMBED_TEXT] Gemini API call successful, embedding dimension: {len(result['embedding'])}")
        return result['embedding']
    except Exception as e:
        logger.error(f"[EMBED_TEXT] FAILED: {e}", exc_info=True)
        raise


async def vector_search(
    query_text: str,
    domain_filter: Optional[str] = None,
    top_k: int = 3,
    collection_name: str = "Embeddings"
) -> List[Dict[str, Any]]:
    """Perform vector search against MongoDB Atlas Vector Search."""
    try:
        logger.info(f"[VECTOR_SEARCH] Starting search - collection: {collection_name}, query: {query_text[:50]}..., domain_filter: {domain_filter}, top_k: {top_k}")
        db = get_db()
        collection = db[collection_name]
        logger.info(f"[VECTOR_SEARCH] Database connection obtained, accessing collection: {collection_name}")
        
        # Generate embedding for query
        logger.info(f"[VECTOR_SEARCH] Generating embedding for query text...")
        query_embedding = await embed_text(query_text)
        logger.info(f"[VECTOR_SEARCH] Embedding generated successfully, dimension: {len(query_embedding)}")
        
        # Build aggregation pipeline with vector search
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index" if collection_name == "Embeddings" else "campus_resource_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": 100,
                    "limit": top_k
                }
            }
        ]
        
        index_name = "vector_index" if collection_name == "Embeddings" else "campus_resource_index"
        logger.info(f"[VECTOR_SEARCH] Using index: {index_name}")
        logger.info(f"[VECTOR_SEARCH] Pipeline stage 1 - $vectorSearch configured")
        
        # Add domain filter if specified
        if domain_filter:
            logger.info(f"[VECTOR_SEARCH] Adding domain filter: {domain_filter}")
            pipeline.append({
                "$match": {"domain": domain_filter}
            })
        
        # Project relevant fields
        logger.info(f"[VECTOR_SEARCH] Adding projection stage")
        pipeline.append({
            "$project": {
                "clause_text": 1,
                "resource_name": 1,
                "description": 1,
                "url": 1,
                "domain": 1,
                "risk_metadata": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        })
        
        logger.info(f"[VECTOR_SEARCH] Executing aggregation pipeline...")
        results = await collection.aggregate(pipeline).to_list(None)
        logger.info(f"[VECTOR_SEARCH] Search completed successfully, found {len(results)} results")
        for i, result in enumerate(results):
            logger.info(f"[VECTOR_SEARCH] Result {i+1}: score={result.get('score', 'N/A')}, domain={result.get('domain', 'N/A')}")
        return results
    except Exception as e:
        logger.error(f"[VECTOR_SEARCH] FAILED: {e}", exc_info=True)
        return []


async def store_clause_embedding(
    session_id: str,
    clause_text: str,
    domain: str,
    risk_metadata: Optional[Dict] = None
) -> bool:
    """Store a clause with its embedding."""
    try:
        logger.info(f"[STORE_EMBEDDING] Starting - session_id: {session_id}, domain: {domain}, clause_length: {len(clause_text)}")
        db = get_db()
        collection = db["Embeddings"]
        logger.info(f"[STORE_EMBEDDING] Accessing Embeddings collection")
        
        logger.info(f"[STORE_EMBEDDING] Generating embedding for clause text...")
        embedding = await embed_text(clause_text)
        logger.info(f"[STORE_EMBEDDING] Embedding generated, dimension: {len(embedding)}")
        
        doc = {
            "session_id": session_id,
            "clause_text": clause_text,
            "embedding": embedding,
            "domain": domain,
            "risk_metadata": risk_metadata or {}
        }
        
        logger.info(f"[STORE_EMBEDDING] Inserting document into Embeddings collection...")
        result = await collection.insert_one(doc)
        success = result.inserted_id is not None
        logger.info(f"[STORE_EMBEDDING] Insert {'successful' if success else 'failed'}, inserted_id: {result.inserted_id}")
        return success
    except Exception as e:
        logger.error(f"[STORE_EMBEDDING] FAILED: {e}", exc_info=True)
        return False


async def seed_campus_resources():
    """Seed campus resources into the vector store."""
    try:
        logger.info(f"[SEED_RESOURCES] Starting campus resources seeding...")
        db = get_db()
        collection = db["campus_resources_vector"]
        logger.info(f"[SEED_RESOURCES] Accessing campus_resources_vector collection")
        
        # Check if already seeded
        logger.info(f"[SEED_RESOURCES] Checking if resources already exist...")
        count = await collection.count_documents({})
        logger.info(f"[SEED_RESOURCES] Found {count} existing resources")
        if count > 0:
            logger.info("[SEED_RESOURCES] Campus resources already seeded, skipping")
            return
        
        resources = [
            {
                "resource_name": "UMass Financial Aid Office",
                "description": "Provides counseling on financial aid packages, FAFSA completion, and aid eligibility",
                "url": "https://www.umass.edu/financialaid",
                "domain": "finance"
            },
            {
                "resource_name": "Student Legal Services Office",
                "description": "Free legal consultations for UMass students on housing, contracts, and disputes",
                "url": "https://www.umass.edu/slso",
                "domain": "housing"
            },
            {
                "resource_name": "International Programs Office",
                "description": "Assists international students with visa, compliance, and work authorization matters",
                "url": "https://www.umass.edu/ipo",
                "domain": "visa"
            },
            {
                "resource_name": "Dean of Students Office",
                "description": "Provides support with academic standing, appeals, and disciplinary matters",
                "url": "https://www.umass.edu/dos",
                "domain": "finance"
            },
            {
                "resource_name": "Housing Support Services",
                "description": "Assists with housing issues, roommate conflicts, and lease questions",
                "url": "https://www.umass.edu/housing",
                "domain": "housing"
            },
            {
                "resource_name": "Bursar's Office",
                "description": "Manages student accounts, billing, payments, and financial holds",
                "url": "https://www.umass.edu/bursar",
                "domain": "finance"
            }
        ]
        
        # Embed and insert
        logger.info(f"[SEED_RESOURCES] Embedding and inserting {len(resources)} resources...")
        for i, resource in enumerate(resources):
            logger.info(f"[SEED_RESOURCES] Processing resource {i+1}/{len(resources)}: {resource['resource_name']}")
            embedding = await embed_text(f"{resource['resource_name']} {resource['description']}")
            resource["embedding"] = embedding
            result = await collection.insert_one(resource)
            logger.info(f"[SEED_RESOURCES] Inserted {resource['resource_name']}, id: {result.inserted_id}")
        
        logger.info(f"[SEED_RESOURCES] Successfully seeded {len(resources)} campus resources")
    except Exception as e:
        logger.error(f"[SEED_RESOURCES] FAILED: {e}", exc_info=True)
