import logging
from typing import Optional
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL
import json

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)


async def classify_document_domain(text: str) -> str:
    """Classify document domain using zero-shot prompting."""
    try:
        prompt = f"""Analyze this document and classify its domain. Return ONLY a JSON object.

Document text:
{text[:2000]}

Respond with ONLY this JSON format (no other text):
{{"domain": "finance|visa|housing|unknown"}}"""
        
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        
        # Parse response
        response_text = response.text.strip()
        
        # Try to extract JSON
        try:
            result = json.loads(response_text)
            domain = result.get("domain", "unknown").lower()
            valid_domains = ["finance", "visa", "housing", "unknown"]
            return domain if domain in valid_domains else "unknown"
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON response: {response_text}")
            # Fallback classification based on keywords
            text_lower = text.lower()
            if any(word in text_lower for word in ["financial", "aid", "fafsa", "loan", "tuition", "scholarship"]):
                return "finance"
            elif any(word in text_lower for word in ["visa", "work authorization", "i-20", "employment", "international"]):
                return "visa"
            elif any(word in text_lower for word in ["lease", "housing", "tenant", "apartment", "rent", "roommate"]):
                return "housing"
            return "unknown"
    except Exception as e:
        logger.error(f"Error classifying document: {e}")
        return "unknown"
