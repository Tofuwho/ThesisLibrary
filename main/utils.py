import fitz  # PyMuPDF
import os
import re
from django.conf import settings
from typing import List, Dict, Tuple, Optional

class PDFSearchEngine:
    """Deep search engine for PDF files using PyMuPDF."""
    
    def __init__(self):
        self.cache = {}  # Simple cache for extracted text
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract all text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        if not os.path.exists(pdf_path):
            return ""
        
        # Check cache first
        if pdf_path in self.cache:
            return self.cache[pdf_path]
        
        try:
            doc = fitz.open(pdf_path)
            text_content = ""
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text_content += page.get_text()
            
            doc.close()
            
            # Cache the result
            self.cache[pdf_path] = text_content
            return text_content
            
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {str(e)}")
            return ""
    
    def search_in_pdf(self, pdf_path: str, query: str) -> Dict:
        """
        Search for a query within a PDF file and return detailed results.
        
        Args:
            pdf_path: Path to the PDF file
            query: Search query
            
        Returns:
            Dictionary with search results including matches and context
        """
        if not os.path.exists(pdf_path):
            return {"found": False, "matches": [], "context": ""}
        
        try:
            doc = fitz.open(pdf_path)
            matches = []
            all_context = []
            
            # Normalize query for case-insensitive search
            query_lower = query.lower()
            query_pattern = re.escape(query_lower)
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text = page.get_text()
                text_lower = text.lower()
                
                # Find all matches in this page
                for match in re.finditer(query_pattern, text_lower):
                    start_pos = match.start()
                    end_pos = match.end()
                    
                    # Get context around the match (50 characters before and after)
                    context_start = max(0, start_pos - 50)
                    context_end = min(len(text), end_pos + 50)
                    context = text[context_start:context_end]
                    
                    # Highlight the match in context
                    highlighted_context = self._highlight_match(context, query, context_start, start_pos)
                    
                    matches.append({
                        "page": page_num + 1,
                        "position": start_pos,
                        "context": highlighted_context,
                        "match_text": text[start_pos:end_pos]
                    })
                    
                    all_context.append(highlighted_context)
            
            doc.close()
            
            return {
                "found": len(matches) > 0,
                "matches": matches,
                "context": " ... ".join(all_context[:3]),  # Limit to first 3 matches
                "total_matches": len(matches)
            }
            
        except Exception as e:
            print(f"Error searching in {pdf_path}: {str(e)}")
            return {"found": False, "matches": [], "context": "", "error": str(e)}
    
    def _highlight_match(self, context: str, query: str, context_start: int, match_start: int) -> str:
        """Highlight the matched text in the context."""
        # Calculate the position of the match within the context
        match_pos_in_context = match_start - context_start
        
        # Find the actual match in the original case
        query_lower = query.lower()
        match_start_in_context = context.lower().find(query_lower, match_pos_in_context)
        
        if match_start_in_context != -1:
            match_end_in_context = match_start_in_context + len(query)
            highlighted = (
                context[:match_start_in_context] +
                f"<mark>{context[match_start_in_context:match_end_in_context]}</mark>" +
                context[match_end_in_context:]
            )
            return highlighted
        
        return context
    
    def get_pdf_preview(self, pdf_path: str, max_pages: int = 3) -> str:
        """
        Get a preview of the PDF content (first few pages).
        
        Args:
            pdf_path: Path to the PDF file
            max_pages: Maximum number of pages to extract
            
        Returns:
            Preview text content
        """
        if not os.path.exists(pdf_path):
            return ""
        
        try:
            doc = fitz.open(pdf_path)
            preview_text = ""
            
            for page_num in range(min(max_pages, doc.page_count)):
                page = doc[page_num]
                preview_text += page.get_text() + "\n\n"
            
            doc.close()
            return preview_text[:1000]  # Limit to 1000 characters
            
        except Exception as e:
            print(f"Error getting preview from {pdf_path}: {str(e)}")
            return ""

# Global instance
pdf_search_engine = PDFSearchEngine()

def search_in_thesis_pdf(thesis, query: str) -> Dict:
    """
    Search for a query within a thesis PDF file.
    
    Args:
        thesis: Thesis model instance
        query: Search query
        
    Returns:
        Search results dictionary
    """
    if not thesis.file:
        return {"found": False, "matches": [], "context": "", "error": "No PDF file available"}
    
    # Get the full path to the PDF file using storage path
    try:
        pdf_path = thesis.file.path
    except Exception:
        # Fallback to joining MEDIA_ROOT and name
        pdf_path = os.path.join(settings.MEDIA_ROOT, thesis.file.name)
    
    return pdf_search_engine.search_in_pdf(pdf_path, query)

def extract_thesis_text(thesis) -> str:
    """
    Extract text content from a thesis PDF.
    
    Args:
        thesis: Thesis model instance
        
    Returns:
        Extracted text content
    """
    if not thesis.file:
        return ""
    
    try:
        pdf_path = thesis.file.path
    except Exception:
        pdf_path = os.path.join(settings.MEDIA_ROOT, thesis.file.name)
    return pdf_search_engine.extract_text_from_pdf(pdf_path)

def get_thesis_preview(thesis, max_pages: int = 3) -> str:
    """
    Get a preview of the thesis content.
    
    Args:
        thesis: Thesis model instance
        max_pages: Maximum number of pages to extract
        
    Returns:
        Preview text content
    """
    if not thesis.file:
        return ""
    
    try:
        pdf_path = thesis.file.path
    except Exception:
        pdf_path = os.path.join(settings.MEDIA_ROOT, thesis.file.name)
    return pdf_search_engine.get_pdf_preview(pdf_path, max_pages)
