import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from models.schemas import UploadResponse
from db.mongo import get_db
from pipelines.extractor import extract_text_from_document, split_into_clauses
from db.vector_store import store_clause_embedding
from config import TEMP_FILE_DIR
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["upload"])


async def process_file_background(
    session_id: str,
    file_path: str,
    file_name: str
):
    """Background task to extract text and process document."""
    try:
        db = get_db()
        
        # Extract text
        text = await extract_text_from_document(file_path)
        
        if not text:
            # Mark as failed
            await db["documents_metadata"].update_one(
                {"_id": session_id},
                {"$set": {"processed_flag": False, "error": "text_extraction_failed"}}
            )
            logger.error(f"Text extraction failed for session {session_id}")
            return
        
        # Split into clauses
        clauses = split_into_clauses(text)
        
        # Store clauses with embeddings
        for i, clause in enumerate(clauses):
            clause_id = f"{session_id}_c{i}"
            await store_clause_embedding(
                session_id=session_id,
                clause_text=clause,
                domain="unknown",
                risk_metadata={"clause_index": i}
            )
        
        # Update document metadata
        await db["documents_metadata"].update_one(
            {"_id": session_id},
            {
                "$set": {
                    "processed_flag": True,
                    "raw_text": text,
                    "clause_count": len(clauses),
                    "processed_timestamp": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Document processing completed for session {session_id}")
        
    except Exception as e:
        logger.error(f"Background processing error: {e}")
        db = get_db()
        await db["documents_metadata"].update_one(
            {"_id": session_id},
            {"$set": {"processed_flag": False, "error": str(e)}}
        )
    finally:
        # Clean up temp file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to clean up temp file: {e}")


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Upload a document for processing."""
    try:
        session_id = str(uuid.uuid4())
        db = get_db()
        
        # Save file temporarily
        os.makedirs(TEMP_FILE_DIR, exist_ok=True)
        file_path = os.path.join(TEMP_FILE_DIR, f"{session_id}_{file.filename}")
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Create document metadata
        doc_metadata = {
            "_id": session_id,
            "user_session_id": session_id,
            "file_name": file.filename,
            "storage_url": f"local://{file_path}",
            "upload_timestamp": datetime.utcnow(),
            "processed_flag": False
        }
        
        await db["documents_metadata"].insert_one(doc_metadata)
        logger.info(f"Document uploaded: {session_id}")
        
        # Queue background processing
        if background_tasks:
            background_tasks.add_task(
                process_file_background,
                session_id,
                file_path,
                file.filename
            )
        
        return UploadResponse(
            session_id=session_id,
            file_name=file.filename,
            status="processing",
            upload_timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise
