import logging
from fastapi import APIRouter, Query
from pydantic import BaseModel
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL
from db.mongo import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


class ChatRequest(BaseModel):
    session_id: str = None
    message: str


class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint for document-related questions."""
    try:
        db = get_db()
        message = request.message
        session_id = request.session_id
        
        # Retrieve document analysis if session exists
        context = ""
        if session_id:
            doc = await db["documents_metadata"].find_one({"_id": session_id})
            if doc and "analysis_results" in doc:
                analysis = doc["analysis_results"]
                domain = analysis.get("domain", "unknown")
                risk_output = analysis.get("risk_output", {})
                summary = risk_output.get("summary", "")
                context = f"""
Document Domain: {domain}
Risk Level: {risk_output.get('risk_level', 'unknown')}
Summary: {summary}
Obligations: {', '.join(risk_output.get('obligations', []))}
"""
        
        # Build prompt
        prompt = f"""You are Navigate413, a helpful assistant for UMass Amherst students understanding complex documents.

{f"Context from uploaded document:{context}" if context else "No document has been uploaded yet."}

User question: {message}

Provide a helpful, concise response (2-3 sentences) that:
- Answers their question directly
- Uses plain language (no jargon)
- Provides actionable advice when applicable
- Suggests contacting Student Legal Services for legal advice when appropriate

Response:"""
        
        # Call Gemini
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        return ChatResponse(response=response_text)
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(response="I encountered an error processing your question. Please try again or contact Student Legal Services for assistance.")
