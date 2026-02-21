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
        result = genai.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            content=text
        )
        return result['embedding']
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise


async def vector_search(
    query_text: str,
    domain_filter: Optional[str] = None,
    top_k: int = 3,
    collection_name: str = "clause_embeddings"
) -> List[Dict[str, Any]]:
    """Perform vector search against MongoDB Atlas Vector Search."""
    try:
        db = get_db()
        collection = db[collection_name]
        
        # Generate embedding for query
        query_embedding = await embed_text(query_text)
        
        # Build aggregation pipeline with vector search
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "clause_vector_index" if collection_name == "clause_embeddings" else "campus_resource_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": 100,
                    "limit": top_k
                }
            }
        ]
        
        # Add domain filter if specified
        if domain_filter:
            pipeline.append({
                "$match": {"domain": domain_filter}
            })
        
        # Project relevant fields
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
        
        results = await collection.aggregate(pipeline).to_list(None)
        return results
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        return []


async def store_clause_embedding(
    session_id: str,
    clause_text: str,
    domain: str,
    risk_metadata: Optional[Dict] = None
) -> bool:
    """Store a clause with its embedding."""
    try:
        db = get_db()
        collection = db["clause_embeddings"]
        
        embedding = await embed_text(clause_text)
        
        doc = {
            "session_id": session_id,
            "clause_text": clause_text,
            "embedding": embedding,
            "domain": domain,
            "risk_metadata": risk_metadata or {}
        }
        
        result = await collection.insert_one(doc)
        return result.inserted_id is not None
    except Exception as e:
        logger.error(f"Failed to store clause embedding: {e}")
        return False


async def seed_campus_resources():
    """Seed campus resources into the vector store."""
    try:
        db = get_db()
        collection = db["campus_resources_vector"]
        
        # Check if already seeded
        count = await collection.count_documents({})
        if count > 0:
            logger.info("Campus resources already seeded")
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
        for resource in resources:
            embedding = await embed_text(f"{resource['resource_name']} {resource['description']}")
            resource["embedding"] = embedding
            await collection.insert_one(resource)
        
        logger.info(f"Seeded {len(resources)} campus resources")
    except Exception as e:
        logger.warning(f"Failed to seed campus resources: {e}")
