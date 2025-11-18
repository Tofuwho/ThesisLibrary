# Search System - Algorithm Documentation

## Overview

This document describes the complete search system used in the Thesis Library, including the two main search modes, the fuzzy correction layer, and how these pieces work together as a hybrid search algorithm.

## Search Modes

### Normal Search Mode (Metadata + Weighted Scoring)

*Purpose*: Fast, metadata-driven search that analyzes thesis card fields without reading PDFs.

#### 1. What Normal Search Inspects

Normal search analyzes only the stored metadata in the database:

1. *Title*
2. *Author*
3. *Abstract*
4. *Keywords*
5. *Research category*
6. *Category name (academic level)*
7. *Department name*
8. *Course name*
9. *Year* (only if the query contains a number)

#### 2. How Normal Search Processes Queries

1. *Tokenization using regex*
   The query is split using the pattern `\w+`, producing lowercase tokens.
   Example: “AI library 2025” → ai, library, 2025.

2. *Weighted field scoring*
   Each token contributes to a relevance score depending on where it appears:

   1. Title → *+8*
   2. Author → *+5*
   3. Abstract → *+3*
   4. Keywords → *+3*
   5. Research category → *+2*
   6. Category name → *+2*
   7. Department name → *+2*
   8. Course name → *+1*
   9. Matching year token → *+2*

3. *Filtering and sorting*

   1. Only theses with a score greater than zero are retained.
   2. Results are ordered first by descending score, then by user-selected sorting (newest year, title alphabetical, author alphabetical).

4. *Fuzzy correction suggestion*

   1. Titles, authors, keywords, research categories, departments, and courses form a suggestion corpus.
   2. RapidFuzz (or difflib fallback) proposes an improved query.
   3. Suggested queries are shown as “Did you mean …?” and may become the effective query.

#### 3. Why Normal Search Is Effective

1. *Relevance-aware scoring* ensures title matches outrank minor matches.
2. *Robust tokenization* finds results even with partial words or mixed concepts.
3. *High performance* since all operations are handled by the database.
4. *User-friendly guidance* through fuzzy suggestions that catch typos.

---

### Deep Search Mode (Full-Text PDF Search)

*Purpose*: Allows users to discover concepts mentioned inside the PDF, not just in metadata.

#### 1. What Deep Search Inspects

Deep search reads the actual PDF text using PyMuPDF (fitz), scanning all pages for literal occurrences of the query.

#### 2. How Deep Search Operates

1. *Apply metadata filters first*
   Only PDFs that match year, department, course, and other filters are scanned.

2. *Optional fuzzy refinement using PDF previews*

   1. Up to 50 filtered theses are sampled.
   2. The early pages of each PDF are extracted using `get_thesis_preview`.
   3. Tokens are generated using the same `\w+` regex.
   4. RapidFuzz determines if a better query exists based on PDF content.
   5. A refined effective query may be used.

3. *Full-text PDF scanning*

   1. Every page is extracted and converted to lowercase.
   2. The query is escaped using `re.escape` and searched using `re.finditer`.
   3. Matches produce:

      1. Page number
      2. Text snippet context
      3. Highlighted match using `<mark>` tags
   4. Only theses with matches are retained.

4. *Attaching deep search metadata*

   1. *deep_search_results* (pages, snippets)
   2. *deep_search_query* (final query used)

#### 3. Result Presentation

Deep search returns a Python list rather than a queryset, allowing the UI to display:

1. Standard thesis card data
2. PDF snippet results and “found in document” indicators

#### 4. Why Deep Search Is Effective

1. *Content-level discovery* for concepts not found in metadata.
2. *High recall* for long or precise phrases.
3. *Context-rich snippets* help users judge relevance instantly.
4. *Balanced performance* by filtering before scanning and limiting preview analysis.

---

## Fuzzy Correction Layer

### Fuzzy Query Correction (Hybrid Layer)

*Purpose*: Improve user queries using real terms found in both metadata and PDF previews.

#### 1. How Fuzzy Suggestion Works

1. The raw query is compared with candidate terms from metadata or PDF content.
2. RapidFuzz scorers used include:

   1. *token_set_ratio*
   2. *partial_ratio*
   3. *WRatio*
3. The system returns:

   1. A proposed corrected phrase
   2. A confidence score
   3. Suppression of low-quality suggestions

#### 2. Benefits of the Fuzzy Layer

1. *Error tolerance* for typos, missing letters, invalid ordering, and spacing mistakes.
2. *Context awareness* because suggestions come from actual stored data.
3. *Transparency* by showing “Did you mean…?” rather than silently altering the results.

---

## Hybrid Search Architecture

### This a Hybrid Search Algorithm

*Yes.* The system combines three separate search mechanisms and their strengths:

1. *Metadata Search (Normal Mode)*
   Weighted, token-based search using field relevance scoring.

2. *Full-Text Content Search (Deep Mode)*
   Literal substring scanning of PDF documents.

3. *Fuzzy Correction Layer*
   Intelligent query refinement using RapidFuzz.

This multi-layer design allows the Thesis Library to deliver relevance, depth, and error tolerance while maintaining performance.