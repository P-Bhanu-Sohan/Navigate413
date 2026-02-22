import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from google import genai
from google.genai import types as genai_types
from config import GEMINI_EMBEDDING_MODEL, GEMINI_API_KEY
from db.mongo import get_db

logger = logging.getLogger(__name__)

# New google-genai client (uses v1 API — required for text-embedding-004)
_genai_client = genai.Client(api_key=GEMINI_API_KEY)


def _embed_text_sync(text: str, task_type: str) -> List[float]:
    """Synchronous Gemini embedding call (run in a thread pool)."""
    response = _genai_client.models.embed_content(
        model=GEMINI_EMBEDDING_MODEL,
        contents=text,
        config=genai_types.EmbedContentConfig(task_type=task_type),
    )
    return response.embeddings[0].values


async def embed_text(text: str, task_type: str = "retrieval_document") -> List[float]:
    """Generate a 768-dim embedding for text using Gemini text-embedding-004.

    Uses asyncio.to_thread so the synchronous genai call does not block
    the event loop.  task_type should be:
      - "retrieval_document" when indexing document clauses
      - "retrieval_query"    when embedding a search query
    """
    try:
        return await asyncio.to_thread(_embed_text_sync, text, task_type)
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise


async def vector_search(
    query_text: str,
    domain_filter: Optional[str] = None,
    top_k: int = 3,
    collection_name: str = "Embeddings"
) -> List[Dict[str, Any]]:
    """Perform vector search against MongoDB Atlas Vector Search."""
    try:
        db = get_db()
        collection = db[collection_name]
        
        # Generate embedding for query (use retrieval_query task type)
        query_embedding = await embed_text(query_text, task_type="retrieval_query")
        
        # Build aggregation pipeline with vector search
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "clause_vector_index" if collection_name == "Embeddings" else "campus_resource_index",
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
        collection = db["Embeddings"]
        
        embedding = await embed_text(clause_text, task_type="retrieval_document")
        
        doc = {
            "session_id": session_id,
            "clause_text": clause_text,
            "embedding": embedding,
            "domain": domain,
            "risk_metadata": risk_metadata or {},
            "created_at": datetime.utcnow(),
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
            embedding = await embed_text(
                f"{resource['resource_name']} {resource['description']}",
                task_type="retrieval_document",
            )
            resource["embedding"] = embedding
            resource["created_at"] = datetime.utcnow()
            await collection.insert_one(resource)
        
        logger.info(f"Seeded {len(resources)} campus resources")
    except Exception as e:
        logger.warning(f"Failed to seed campus resources: {e}")
