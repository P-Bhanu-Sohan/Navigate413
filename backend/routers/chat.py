import logging
from fastapi import APIRouter, Query
from pydantic import BaseModel
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL
from db.mongo import get_db
from tools.retrieval_tool import GlobalRetrievalTool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


class ChatRequest(BaseModel):
    session_id: str = None
    message: str
    language: str = "English"  # Target language for response


class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint for document-related questions with RAG context."""
    try:
        print(f"\n💬 [CHAT] Received message: {request.message[:50]}...")
        
        db = get_db()
        message = request.message
        session_id = request.session_id
        
        # Retrieve document analysis if session exists
        doc_context = ""
        if session_id:
            print(f"💬 [CHAT] Looking up session: {session_id}")
            doc = await db["documents_metadata"].find_one({"_id": session_id})
            if doc and "analysis_results" in doc:
                analysis = doc["analysis_results"]
                domain = analysis.get("domain", "unknown")
                risk_output = analysis.get("risk_output", {})
                summary = risk_output.get("summary", "")
                doc_context = f"""
Document Domain: {domain}
Risk Level: {risk_output.get('risk_level', 'unknown')}
Summary: {summary}
Obligations: {', '.join(risk_output.get('obligations', []))}
"""
                print(f"💬 [CHAT] Found document context for domain: {domain}")
        
        # Check if this is a resource-related question
        resource_keywords = ['resource', 'help', 'office', 'contact', 'where', 'who', 'support', 'assistance', 'services']
        is_resource_question = any(kw in message.lower() for kw in resource_keywords)
        
        # RAG: Search campus_embeddings collection for similar clauses
        print(f"💬 [CHAT] Searching campus_embeddings collection for: {message[:50]}...")
        rag_results = await GlobalRetrievalTool(
            query_text=message,
            domain_filter=None,
            top_k=5,
            collection_type="clause"
        )
        
        print(f"💬 [CHAT] RAG retrieved {len(rag_results)} similar clauses")
        
        # Format RAG context with FULL clause text for better responses
        rag_context = ""
        if rag_results:
            rag_clauses = []
            for i, result in enumerate(rag_results[:5], 1):
                clause_text = result.get("clause_text", "")
                score = result.get("score", 0)
                risk_metadata = result.get("risk_metadata", {})
                if clause_text:
                    clause_entry = f"\n[CLAUSE {i}] (Relevance: {score:.2f})\n{clause_text}"
                    if risk_metadata:
                        clause_entry += f"\n[Risk Flag: {risk_metadata.get('flag', 'N/A')}]"
                    rag_clauses.append(clause_entry)
            
            if rag_clauses:
                rag_context = "\n\n=== RELEVANT DOCUMENT CLAUSES ==="
                rag_context += "".join(rag_clauses)
                rag_context += "\n=== END CLAUSES ==="
                print(f"💬 [CHAT] Injected {len(rag_clauses)} FULL clauses into context")
        
        # Add UMass campus resources for resource questions
        if is_resource_question:
            print(f"💬 [CHAT] Detected resource question, adding campus resources")
            rag_context += """

=== UMASS CAMPUS RESOURCES ===
[HOUSING RESOURCES]
- Student Legal Services Office (SLSO): Free legal help for lease disputes, tenant rights - https://www.umass.edu/slso - 413-545-1995
- Off-Campus Student Services: Housing assistance, roommate mediation - https://www.umass.edu/offcampus
- Residential Life: On-campus housing issues - https://www.umass.edu/living

[FINANCIAL AID RESOURCES]
- Financial Aid Services: FAFSA help, aid appeals, payment plans - https://www.umass.edu/financialaid - 413-545-0801
- Bursar's Office: Billing, tuition payments - https://www.umass.edu/bursar
- Student Financial Strategies: Emergency loans, financial counseling - https://www.umass.edu/financialstrategies

[INTERNATIONAL STUDENT RESOURCES]
- International Programs Office (IPO): Visa issues, work authorization, SEVIS - https://www.umass.edu/ipo - 413-545-2710
- International Students & Scholars Services: Immigration advising

[GENERAL SUPPORT]
- Dean of Students: Academic and personal support - https://www.umass.edu/dean_students
- Center for Counseling and Psychological Health: Free mental health services - https://www.umass.edu/counseling
=== END RESOURCES ==="""
        
        # Build enhanced prompt with RAG context
        target_language = request.language if hasattr(request, 'language') else "English"
        
        prompt = f"""You are Navigate413, an expert document assistant for UMass Amherst students.

{f"CURRENT DOCUMENT:{doc_context}" if doc_context else "No document uploaded."}
{rag_context}

QUESTION (in English): {message}

CRITICAL RULES:
1. READ THE CLAUSES THOROUGHLY - Extract exact numbers, dates, and terms
2. BE CONCISE - Answer in 2-3 sentences maximum
3. BE DIRECT - Start with the answer immediately, no preamble
4. BE SPECIFIC - Quote exact amounts (e.g., $2,000, not "two thousand dollars")
5. ONLY answer what was asked - don't add extra information unless critical
6. If info is missing from clauses, say "Not specified in the document" and stop
7. Use <b>bold tags</b> for important numbers and terms (NOT markdown asterisks)
8. RESPOND IN {target_language} - The user will ask in English but you must answer in {target_language}

FORMAT: [Direct answer with specifics] [Legal reference if present] [Brief implication if critical]

RESPONSE IN {target_language}:"""
        
        # Call Gemini
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        return ChatResponse(response=response_text)
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(response="I encountered an error processing your question. Please try again or contact Student Legal Services for assistance.")
