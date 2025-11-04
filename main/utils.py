import fitz  # PyMuPDF
import os
import re
from django.conf import settings
from typing import List, Dict, Tuple, Optional
try:
    # RapidFuzz provides much stronger fuzzy matching than difflib
    from rapidfuzz import fuzz, process
except Exception:  # Optional dependency; views should still work without it
    fuzz = None
    process = None

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


def suggest_query_correction(query: str, candidates: List[str]) -> Tuple[Optional[str], float]:
    """Return a robust fuzzy suggestion for a possibly misspelled query.

    Uses RapidFuzz token-based scores to better handle missing letters and jumbled words.

    Args:
        query: Raw user-entered search text
        candidates: List of candidate strings to match against

    Returns:
        (suggestion, confidence) where suggestion may be None if no good match
    """
    if not query or not candidates:
        return (None, 0.0)

    # Filter out empty/None candidates and keep insertion order
    seen = set()
    corpus_unique: List[str] = []
    for c in candidates:
        if not c:
            continue
        if c not in seen:
            seen.add(c)
            corpus_unique.append(c)

    # If RapidFuzz is not available, fall back to a simple heuristic
    if process is None or fuzz is None:
        try:
            import difflib
            match = difflib.get_close_matches(query, corpus_unique, n=1, cutoff=0.8)
            if match:
                return (match[0], 0.8)
            # Token-wise fallback
            tokens = [t for t in re.findall(r"\w+", query) if t.strip()]
            suggested_tokens: List[str] = []
            for tkn in tokens:
                m = difflib.get_close_matches(tkn, corpus_unique, n=1, cutoff=0.75)
                suggested_tokens.append(m[0] if m else tkn)
            suggestion_joined = " ".join(suggested_tokens).strip()
            if suggestion_joined and suggestion_joined.lower() != query.strip().lower():
                return (suggestion_joined, 0.75)
            return (None, 0.0)
        except Exception:
            return (None, 0.0)

    # Use a weighted strategy that is resilient to missing/jumbled letters and token order
    # 1) Whole-phrase best match using token_set_ratio (handles rearranged/missing tokens)
    best_phrase = process.extractOne(
        query,
        corpus_unique,
        scorer=fuzz.token_set_ratio,
        score_cutoff=70,  # tolerate errors; tuneable
    )

    # 2) Token-wise correction then join, using partial_ratio to survive missing letters
    tokens = [t for t in re.findall(r"\w+", query) if t.strip()]
    suggested_tokens: List[str] = []
    token_scores: List[float] = []
    for tkn in tokens:
        tok_match = process.extractOne(
            tkn,
            corpus_unique,
            scorer=fuzz.partial_ratio,
            score_cutoff=65,
        )
        if tok_match:
            suggested_tokens.append(tok_match[0])
            token_scores.append(float(tok_match[1]))
        else:
            suggested_tokens.append(tkn)
            token_scores.append(50.0)

    token_joined = " ".join(suggested_tokens).strip() if suggested_tokens else ""
    token_conf = sum(token_scores) / len(token_scores) if token_scores else 0.0

    # Decide which suggestion to use
    chosen_suggestion = None
    chosen_conf = 0.0

    if best_phrase:
        chosen_suggestion = best_phrase[0]
        chosen_conf = float(best_phrase[1]) / 100.0

    if token_joined and token_joined.lower() != query.strip().lower():
        # Compare combined token-based suggestion against phrase-based one using WRatio
        joined_score = fuzz.WRatio(query, token_joined) / 100.0
        if joined_score > chosen_conf + 0.05:  # prefer better by margin
            chosen_suggestion = token_joined
            chosen_conf = joined_score

    # Avoid suggesting if confidence is low or suggestion equals original (case-insensitive)
    if not chosen_suggestion:
        return (None, 0.0)
    if chosen_suggestion.strip().lower() == query.strip().lower():
        return (None, 0.0)
    if chosen_conf < 0.7:  # tuneable threshold
        return (None, chosen_conf)

    return (chosen_suggestion, chosen_conf)


def deep_filter_theses_by_pdf(theses: List, query: str) -> List:
    """Return only theses whose PDF contains the query.

    Attaches `deep_search_results` and `deep_search_query` attributes to each
    matched thesis for downstream rendering. This does not look at metadata
    fields; it strictly searches PDF text content.
    """
    if not query:
        return []

    matched: List = []
    for thesis in theses:
        if not getattr(thesis, 'file', None):
            continue
        results = search_in_thesis_pdf(thesis, query)
        if results.get('found'):
            thesis.deep_search_results = results
            thesis.deep_search_query = query
            matched.append(thesis)
    return matched
