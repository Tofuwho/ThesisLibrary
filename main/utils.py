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


def extract_abstract_from_pdf(pdf_file) -> str:
    """
    Extract abstract from a PDF file.
    
    This function looks for the abstract section in the first few pages of the PDF.
    It searches for common abstract markers like "Abstract", "ABSTRACT", etc.
    
    Args:
        pdf_file: Django UploadedFile or file path
        
    Returns:
        Extracted abstract text, or empty string if not found
    """
    try:
        # Handle both file path and Django UploadedFile
        if hasattr(pdf_file, 'read'):
            # It's a Django UploadedFile - save temporarily
            import tempfile
            # Reset file to beginning if possible (for InMemoryUploadedFile)
            if hasattr(pdf_file, 'seek'):
                try:
                    pdf_file.seek(0)
                except:
                    pass
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                for chunk in pdf_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            pdf_path = tmp_file_path
            should_delete = True
            
            # Reset file pointer to beginning for Django to save it properly
            if hasattr(pdf_file, 'seek'):
                try:
                    pdf_file.seek(0)
                except:
                    pass
        else:
            # It's a file path
            pdf_path = pdf_file
            should_delete = False
        
        if not os.path.exists(pdf_path):
            return ""
        
        doc = fitz.open(pdf_path)
        abstract_text = ""
        
        # Search in first 5 pages (abstract is usually in early pages)
        search_pages = min(5, doc.page_count)
        
        for page_num in range(search_pages):
            page = doc[page_num]
            text = page.get_text()
            
            # Look for abstract section markers
            abstract_patterns = [
                r'(?i)\babstract\b',
                r'(?i)\bsummary\b',
                r'(?i)\bexecutive\s+summary\b',
            ]
            
            # Find where abstract section starts
            abstract_start = -1
            for pattern in abstract_patterns:
                match = re.search(pattern, text)
                if match:
                    abstract_start = match.end()
                    break
            
            if abstract_start != -1:
                # Extract text after "Abstract" marker
                potential_abstract = text[abstract_start:].strip()
                
                # Remove common headers/footers and clean up
                lines = potential_abstract.split('\n')
                cleaned_lines = []
                skip_next = False
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Skip common headers/footers
                    if re.match(r'^(page|p\.?)\s*\d+', line, re.I):
                        continue
                    if re.match(r'^\d+$', line):  # Page numbers alone
                        continue
                    
                    # Stop at common section markers (Introduction, Chapter 1, etc.)
                    if re.search(r'(?i)^(introduction|chapter\s+[1-9]|table\s+of\s+contents|acknowledgment|acknowledgement|references|bibliography)', line):
                        break
                    
                    cleaned_lines.append(line)
                    
                    # Limit abstract length (typically 150-500 words)
                    if len(' '.join(cleaned_lines).split()) > 600:
                        break
                
                abstract_text = ' '.join(cleaned_lines)
                
                # Clean up extra whitespace
                abstract_text = re.sub(r'\s+', ' ', abstract_text).strip()
                
                # If we found a reasonable abstract (at least 50 words), return it
                if len(abstract_text.split()) >= 50:
                    doc.close()
                    if should_delete and os.path.exists(pdf_path):
                        os.unlink(pdf_path)
                    return abstract_text
        
        # If no abstract marker found, try extracting first substantial paragraph
        # from early pages (often the abstract is the first substantial text)
        if not abstract_text:
            for page_num in range(min(3, doc.page_count)):
                page = doc[page_num]
                text = page.get_text()
                
                # Split into paragraphs
                paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
                
                for para in paragraphs:
                    # Skip very short paragraphs (likely headers/footers)
                    if len(para.split()) < 30:
                        continue
                    
                    # Skip paragraphs that look like headers
                    if len(para.split('\n')) > 5:  # Too many line breaks
                        continue
                    
                    # Skip if contains common non-abstract content
                    if re.search(r'(?i)(table\s+of\s+contents|chapter|page\s+\d+)', para):
                        continue
                    
                    # Found a substantial paragraph - likely the abstract
                    abstract_text = re.sub(r'\s+', ' ', para).strip()
                    if len(abstract_text.split()) >= 50:
                        doc.close()
                        if should_delete and os.path.exists(pdf_path):
                            os.unlink(pdf_path)
                        return abstract_text
        
        doc.close()
        if should_delete and os.path.exists(pdf_path):
            os.unlink(pdf_path)
        
        return abstract_text
        
    except Exception as e:
        print(f"Error extracting abstract from PDF: {str(e)}")
        if should_delete and 'pdf_path' in locals() and os.path.exists(pdf_path):
            try:
                os.unlink(pdf_path)
            except:
                pass
        return ""


def extract_title_from_pdf(pdf_file) -> str:
    """
    Extract title from a PDF file.
    
    This function extracts the title from the first page of the PDF, prioritizing
    bold text and excluding logo/header text. Titles are typically bold and located
    near the top of the first page.
    
    Args:
        pdf_file: Django UploadedFile or file path
        
    Returns:
        Extracted title text, or empty string if not found
    """
    try:
        # Handle both file path and Django UploadedFile
        if hasattr(pdf_file, 'read'):
            # It's a Django UploadedFile - save temporarily
            import tempfile
            # Reset file to beginning if possible (for InMemoryUploadedFile)
            if hasattr(pdf_file, 'seek'):
                try:
                    pdf_file.seek(0)
                except:
                    pass
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                for chunk in pdf_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            pdf_path = tmp_file_path
            should_delete = True
            
            # Reset file pointer to beginning for Django to save it properly
            if hasattr(pdf_file, 'seek'):
                try:
                    pdf_file.seek(0)
                except:
                    pass
        else:
            # It's a file path
            pdf_path = pdf_file
            should_delete = False
        
        if not os.path.exists(pdf_path):
            return ""
        
        doc = fitz.open(pdf_path)
        title_text = ""
        
        # Extract from first page only
        if doc.page_count > 0:
            first_page = doc[0]
            text_dict = first_page.get_text("dict")
            page_rect = first_page.rect
            page_height = page_rect.height
            
            # Collect all text lines with their properties (bold, position, font size)
            all_lines = []
            
            for block in text_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        line_text_parts = []
                        line_y_position = None
                        line_is_bold = False
                        line_font_size = 0
                        line_bbox = None
                        
                        for span in line.get("spans", []):
                            text_content = span.get("text", "").strip()
                            if not text_content:
                                continue
                            
                            # Get font properties
                            font_size = span.get("size", 0)
                            flags = span.get("flags", 0)
                            is_bold = bool(flags & 16)  # Bit 4 (16) indicates bold
                            
                            # Get position (y-coordinate - top of span)
                            bbox = span.get("bbox", [0, 0, 0, 0])
                            y_position = bbox[1] if len(bbox) > 1 else 0
                            
                            if not line_y_position:
                                line_y_position = y_position
                                line_bbox = bbox
                            
                            # Track if any part of the line is bold
                            if is_bold:
                                line_is_bold = True
                            
                            # Track largest font size in line
                            if font_size > line_font_size:
                                line_font_size = font_size
                            
                            line_text_parts.append(text_content)
                        
                        if line_text_parts:
                            full_line_text = ' '.join(line_text_parts)
                            full_line_text = re.sub(r'\s+', ' ', full_line_text).strip()
                            
                            # Skip empty or very short lines
                            if len(full_line_text) < 5:
                                continue
                            
                            # Skip page numbers and headers
                            if re.match(r'^(page|p\.?)\s*\d+', full_line_text, re.I):
                                continue
                            if re.match(r'^\d+$', full_line_text):
                                continue
                            
                            # Skip filenames (contains .pdf, path separators, etc.)
                            if re.search(r'\.(pdf|doc|docx|txt)$', full_line_text, re.I):
                                continue
                            if '/' in full_line_text or '\\' in full_line_text:
                                continue
                            
                            # Skip common non-title patterns (abstract, TOC, etc.)
                            if re.search(r'(?i)^(abstract|table\s+of\s+contents|acknowledgment|acknowledgement|introduction|chapter\s+[1-9]|references|bibliography|by:?|presented\s+to)', full_line_text):
                                continue
                            
                            all_lines.append({
                                'text': full_line_text,
                                'is_bold': line_is_bold,
                                'font_size': line_font_size,
                                'y_position': line_y_position,
                                'bbox': line_bbox
                            })
            
            # Group consecutive bold lines that are close together (multi-line titles)
            bold_groups = []
            current_group = []
            
            for i, line in enumerate(all_lines):
                if line['is_bold']:
                    # Check if this line should be grouped with the previous bold line
                    if current_group:
                        prev_line = current_group[-1]
                        # Group if lines are close vertically (within reasonable distance)
                        y_diff = abs(line['y_position'] - prev_line['y_position'])
                        # Typical line spacing is around 15-25 points, allow up to 40 for title wrapping
                        if y_diff < 40:
                            current_group.append(line)
                        else:
                            # Start a new group
                            if current_group:
                                bold_groups.append(current_group)
                            current_group = [line]
                    else:
                        current_group = [line]
                else:
                    # Non-bold line - end current group if exists
                    if current_group:
                        bold_groups.append(current_group)
                        current_group = []
            
            # Add last group if exists
            if current_group:
                bold_groups.append(current_group)
            
            # Process bold groups to create title candidates
            text_candidates = []
            top_threshold = page_height * 0.12  # Top 12% is likely logo area
            
            for group in bold_groups:
                # Combine all lines in the group
                group_text = ' '.join([line['text'] for line in group])
                group_text = re.sub(r'\s+', ' ', group_text).strip()
                
                # Get properties from the first line in group
                first_line = group[0]
                y_pos = first_line['y_position']
                font_size = first_line['font_size']
                
                # Filter out logo/header text
                is_likely_logo = False
                
                if y_pos < top_threshold:
                    # Very short text at top is likely logo/header
                    if len(group_text) < 20:
                        is_likely_logo = True
                    # Short all-caps text at top is likely logo (but longer all-caps might be title)
                    elif group_text.isupper() and len(group_text) < 50:
                        is_likely_logo = True
                    # Contains common logo/header words
                    elif re.search(r'(?i)^(university|college|institute|department|faculty|school)\s+(of|at)', group_text):
                        is_likely_logo = True
                
                # Skip if it's likely a logo
                if is_likely_logo:
                    continue
                
                # Valid title candidate - check length (titles are usually 10-300 chars)
                if 10 <= len(group_text) <= 500:
                    # Calculate score: bold text gets higher priority
                    score = 200  # Bold groups get high base score
                    
                    # Larger font size gets higher priority
                    score += font_size * 2
                    
                    # Longer text gets slightly higher priority (titles are usually substantial)
                    score += min(len(group_text) / 10, 20)
                    
                    # Text below logo area gets higher priority
                    if y_pos > top_threshold:
                        score += 50
                    
                    text_candidates.append({
                        'text': group_text,
                        'score': score,
                        'is_bold': True,
                        'font_size': font_size,
                        'y_position': y_pos,
                        'length': len(group_text)
                    })
            
            # Also add individual bold lines that weren't grouped (in case title is single line)
            for line in all_lines:
                if line['is_bold'] and 10 <= len(line['text']) <= 500:
                    # Check if this line is already in a group
                    already_grouped = False
                    for group in bold_groups:
                        if any(l['text'] == line['text'] for l in group):
                            already_grouped = True
                            break
                    
                    if not already_grouped:
                        # Filter logo
                        is_likely_logo = False
                        if line['y_position'] < top_threshold:
                            if len(line['text']) < 20:
                                is_likely_logo = True
                            elif line['text'].isupper() and len(line['text']) < 50:
                                is_likely_logo = True
                            elif re.search(r'(?i)^(university|college|institute|department|faculty|school)\s+(of|at)', line['text']):
                                is_likely_logo = True
                        
                        if not is_likely_logo:
                            score = 150  # Slightly lower than groups
                            score += line['font_size'] * 2
                            score += min(len(line['text']) / 10, 20)
                            if line['y_position'] > top_threshold:
                                score += 50
                            
                            text_candidates.append({
                                'text': line['text'],
                                'score': score,
                                'is_bold': True,
                                'font_size': line['font_size'],
                                'y_position': line['y_position'],
                                'length': len(line['text'])
                            })
            
            # Sort candidates by score (highest first)
            text_candidates.sort(key=lambda x: x['score'], reverse=True)
            
            # Select the best candidate
            # Prioritize bold text that's substantial in length and below logo area
            for candidate in text_candidates:
                text = candidate['text']
                y_pos = candidate['y_position']
                
                # Best case: bold, substantial length, below logo area
                if candidate['is_bold'] and len(text) >= 30 and y_pos > top_threshold:
                    title_text = text
                    break
                # Second best: bold, substantial length, even if at top
                elif candidate['is_bold'] and len(text) >= 30:
                    title_text = text
                    break
            
            # If still no title, use the highest scoring candidate
            if not title_text and text_candidates:
                title_text = text_candidates[0]['text']
        
        doc.close()
        if should_delete and os.path.exists(pdf_path):
            os.unlink(pdf_path)
        
        return title_text
        
    except Exception as e:
        print(f"Error extracting title from PDF: {str(e)}")
        if 'should_delete' in locals() and should_delete and 'pdf_path' in locals() and os.path.exists(pdf_path):
            try:
                os.unlink(pdf_path)
            except:
                pass
        return ""


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
        print(f"DEBUG: empty query ({query}) or candidates")
        return (None, 0.0)

    try:
        from main.nlp_utils import get_english_dictionary_words
        dict_words = get_english_dictionary_words()
    except Exception:
        dict_words = set()

    # Filter out empty/None candidates and keep insertion order
    seen = set()
    corpus_unique: List[str] = []
    word_corpus = set()
    for c in candidates:
        if not c:
            continue
        if c not in seen:
            seen.add(c)
            corpus_unique.append(c)
            # Add individual words to word_corpus for token-by-token comparison
            for w in re.findall(r"\w+", c.lower()):
                word_corpus.add(w)

    for w in dict_words:
        word_corpus.add(w.lower())

    word_corpus_list = list(word_corpus)

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
                m = difflib.get_close_matches(tkn, word_corpus_list, n=1, cutoff=0.75)
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

    # 2) Token-wise correction then join, using standard ratio to account for length differences (partial_ratio breaks on single letters)
    tokens = [t for t in re.findall(r"\w+", query) if t.strip()]
    suggested_tokens: List[str] = []
    token_scores: List[float] = []
    for tkn in tokens:
        # For very short tokens, we don't want fuzzy matching to blindly suggest longer random words
        # but fuzz.ratio naturally handles this by penalizing length differences
        tok_match = process.extractOne(
            tkn,
            word_corpus_list,
            scorer=fuzz.ratio,
            score_cutoff=70,  # raised cutoff slightly to ensure better matches
        )
        if tok_match:
            suggested_tokens.append(tok_match[0])
            token_scores.append(float(tok_match[1]))
        else:
            suggested_tokens.append(tkn)
            token_scores.append(100.0) # Assume exact match/correct word if no fuzzy match found (keeps original word)

    token_joined = " ".join(suggested_tokens).strip() if suggested_tokens else ""
    token_conf = sum(token_scores) / len(token_scores) if token_scores else 0.0

    # Decidide which suggestion to use
    chosen_suggestion = None
    chosen_conf = 0.0

    # 3. Dedicated Acronym Mapping for Library/University (CCT -> CICT, etc.)
    ACRONYM_MAP = {
        'cct': 'cict',
        'cict': 'cict',
        'cas': 'cas',
        'cba': 'cba',
        'coe': 'coe',
        'chm': 'chm',
        'ced': 'ced',
        'tcu': 'tcu',
        'lib': 'library'
    }
    
    # Check if query itself or tokens are in acronym map
    query_norm = query.strip().lower()
    if query_norm in ACRONYM_MAP:
        return (ACRONYM_MAP[query_norm], 1.0)

    if best_phrase:
        chosen_suggestion = best_phrase[0]
        chosen_conf = float(best_phrase[1]) / 100.0

    if token_joined and token_joined.lower() != query.strip().lower():
        # Compare combined token-based suggestion against phrase-based one using WRatio
        joined_score = fuzz.WRatio(query, token_joined) / 100.0
        # If the joined token score is high (it corrected typos well), prefer it over the phrase matcher
        if joined_score > chosen_conf or (chosen_suggestion and len(chosen_suggestion.split()) != len(tokens)):
            chosen_suggestion = token_joined
            chosen_conf = max(chosen_conf, joined_score)

    # Avoid suggesting if confidence is low or suggestion equals original (case-insensitive)
    if not chosen_suggestion:
        return (None, 0.0)
    if chosen_suggestion.strip().lower() == query.strip().lower():
        return (None, 0.0)
    if chosen_conf < 0.7:
        return (None, chosen_conf)

    print(f"DEBUG utils.py - Suggestion for '{query}' -> '{chosen_suggestion}' (conf {chosen_conf})")
    return (chosen_suggestion, chosen_conf)


def deep_filter_theses_by_pdf(theses: List, query: str) -> List:
    """Return theses whose PDF contains the query, sorted by frequency."""
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
            # Attachment for sorting
            thesis.match_count = results.get('total_matches', 1)
            matched.append(thesis)
            
    # Sort by number of matches found in PDF (most relevant first)
    matched.sort(key=lambda x: x.match_count, reverse=True)
    return matched
