import logging
import os
from typing import List, Optional
import pdfplumber
import nltk
from pathlib import Path

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


async def extract_text_from_pdf(file_path: str) -> Optional[str]:
    """Extract text from PDF using pdfplumber."""
    try:
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        if len(text.strip()) > 100:
            logger.info(f"Extracted {len(text)} characters using pdfplumber")
            return text.strip()
        else:
            logger.info("Text extraction yielded < 100 chars, likely scanned document")
            return None
    except Exception as e:
        logger.error(f"Error extracting text with pdfplumber: {e}")
        return None


async def extract_text_with_ocr(file_path: str) -> Optional[str]:
    """Extract text from scanned PDF using pytesseract."""
    try:
        from pdf2image import convert_from_path
        import pytesseract
        
        images = convert_from_path(file_path)
        text = ""
        
        for i, image in enumerate(images):
            page_text = pytesseract.image_to_string(image)
            if page_text:
                text += page_text + "\n"
        
        if len(text.strip()) > 100:
            logger.info(f"Extracted {len(text)} characters using OCR")
            return text.strip()
        else:
            logger.info("OCR extraction yielded < 100 chars")
            return None
    except Exception as e:
        logger.error(f"Error extracting text with OCR: {e}")
        return None


async def extract_text_from_document(file_path: str) -> Optional[str]:
    """Extract text from document, trying pdfplumber first, then OCR."""
    # Try standard PDF extraction first
    text = await extract_text_from_pdf(file_path)
    
    if text:
        return text
    
    # Fall back to OCR for scanned documents
    logger.info("Attempting OCR extraction")
    text = await extract_text_with_ocr(file_path)
    return text


def split_into_clauses(text: str, chunk_size: int = 3) -> List[str]:
    """Split extracted text into clause chunks using sentence tokenization."""
    try:
        sentences = nltk.sent_tokenize(text)
        clauses = []
        
        for i in range(0, len(sentences), chunk_size):
            clause = " ".join(sentences[i:i+chunk_size])
            if clause.strip():
                clauses.append(clause.strip())
        
        logger.info(f"Split text into {len(clauses)} clauses")
        return clauses
    except Exception as e:
        logger.error(f"Error splitting into clauses: {e}")
        # Fallback: split by newlines
        return [line.strip() for line in text.split('\n') if line.strip()]
