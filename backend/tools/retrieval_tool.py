import logging
from typing import Optional, List, Dict, Any
from db.vector_store import vector_search

logger = logging.getLogger(__name__)


async def GlobalRetrievalTool(
    query_text: str,
    domain_filter: Optional[str] = None,
    campus: str = "UMass",
    top_k: int = 3,
    collection_type: str = "clause"  # "clause" or "resource"
) -> List[Dict[str, Any]]:
    """
    Universal retrieval tool for semantic search.
    Returns relevant clauses or campus resources based on query.
    
    Args:
        query_text: The semantic query
        domain_filter: Optional domain filter (finance, visa, housing)
        campus: Campus name (default: UMass)
        top_k: Number of results to return
        collection_type: Type of collection to search ("clause" or "resource")
    
    Returns:
        List of relevant documents with scores
    """
    try:
        collection_name = "clause_embeddings" if collection_type == "clause" else "campus_resources_vector"
        
        results = await vector_search(
            query_text=query_text,
            domain_filter=domain_filter,
            top_k=top_k,
            collection_name=collection_name
        )
        
        logger.info(f"GlobalRetrievalTool returned {len(results)} results for query")
        return results
    except Exception as e:
        logger.error(f"GlobalRetrievalTool error: {e}")
        return []
