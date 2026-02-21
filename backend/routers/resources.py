import logging
from fastapi import APIRouter, Query
from models.schemas import ResourceQueryResponse, Resource
from tools.retrieval_tool import GlobalRetrievalTool
from db.mongo import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["resources"])


@router.get("/resources", response_model=ResourceQueryResponse)
async def get_resources(
    query: str = Query(...),
    domain: str = Query(None),
    top_k: int = Query(3, ge=1, le=10)
):
    """Search for relevant campus resources."""
    try:
        results = await GlobalRetrievalTool(
            query_text=query,
            domain_filter=domain,
            top_k=top_k,
            collection_type="resource"
        )
        
        # Convert to Resource objects
        resources = []
        for result in results:
            resources.append(Resource(
                name=result.get("resource_name", ""),
                url=result.get("url", ""),
                relevance=result.get("score", 0.0),
                description=result.get("description", "")
            ))
        
        return ResourceQueryResponse(results=resources)
    except Exception as e:
        logger.error(f"Resource search error: {e}")
        return ResourceQueryResponse(results=[])


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Retrieve full stored analysis result for a session."""
    try:
        db = get_db()
        doc = await db["documents_metadata"].find_one({"_id": session_id})
        
        if not doc:
            return {"error": "Session not found"}
        
        return doc
    except Exception as e:
        logger.error(f"Session retrieval error: {e}")
        raise
