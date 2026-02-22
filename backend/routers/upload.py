import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from models.schemas import UploadResponse
from db.mongo import get_db
from pipelines.extractor import extract_text_from_document, split_into_clauses
from db.vector_store import store_clause_embedding
from config import TEMP_FILE_DIR
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["upload"])




@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a document, extract text inline, and store metadata."""
    temp_file_path = None
    
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        session_id = str(uuid.uuid4())
        db = get_db()
        
        # Read file content
        content = await file.read()
        
        # Validate file size (50MB max)
        max_size_bytes = 50 * 1024 * 1024
        if len(content) > max_size_bytes:
            raise HTTPException(status_code=413, detail="File size exceeds 50MB limit")
        
        # Save to temporary file for extraction
        os.makedirs(TEMP_FILE_DIR, exist_ok=True)
        temp_file_path = os.path.join(TEMP_FILE_DIR, f"{session_id}_{file.filename}")
        
        with open(temp_file_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"Saved temp file for extraction: {session_id}")
        
        # Extract text inline (synchronous)
        text = await extract_text_from_document(temp_file_path)
        
        if not text or len(text.strip()) < 100:
            raise HTTPException(
                status_code=422,
                detail="Text extraction failed. Please upload a text-based PDF or ensure the document is readable."
            )
        
        logger.info(f"Extracted {len(text)} characters for session {session_id}")
        
        # Split into clauses
        clauses = split_into_clauses(text)
        
        # Store clauses with embeddings
        for i, clause in enumerate(clauses):
            await store_clause_embedding(
                session_id=session_id,
                clause_text=clause,
                domain="unknown",
                risk_metadata={"clause_index": i}
            )
        
        logger.info(f"Stored {len(clauses)} clause embeddings for session {session_id}")
        
        # Create document metadata with extracted text
        doc_metadata = {
            "_id": session_id,
            "user_session_id": session_id,
            "file_name": file.filename,
            "upload_timestamp": datetime.utcnow(),
            "processed_flag": True,
            "raw_text": text,
            "clause_count": len(clauses),
            "processed_timestamp": datetime.utcnow(),
            "status": "completed"
        }
        
        await db["documents_metadata"].insert_one(doc_metadata)
        logger.info(f"Document processing completed for session {session_id}")
        
        return UploadResponse(
            session_id=session_id,
            file_name=file.filename,
            status="completed",
            upload_timestamp=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload/extraction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
    finally:
        # Always clean up temp file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"Cleaned up temp file for session {session_id}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")
