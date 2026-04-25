import re
from django.db.models import Q, F, Value, IntegerField, Case, When, ExpressionWrapper, CharField
from django.db.models.functions import Concat
from .models import Thesis, Department, Course, Category
from .utils import suggest_query_correction, get_thesis_preview, search_in_thesis_pdf, pdf_search_engine

STOPWORDS = {
    'a', 'an', 'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'as', 
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 
    'did', 'but', 'if', 'then', 'else', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 
    'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 
    'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 
    'should', 'now', 'thesis', 'study', 'research', 'library'
}

PHRASE_WEIGHTS = {
    'title': 150,
    'abstract': 100,
    'author': 80,
    'keywords': 80,
    'coauthor': 70,
    'department': 50,
    'course': 40
}

TOKEN_WEIGHTS = {
    'title': 30,
    'author': 15,
    'coauthor': 15,
    'abstract': 10,
    'keywords': 10,
    'research_cat': 5,
    'cat_name': 5,
    'dept_name': 5,
    'course_name': 5,
    'year': 20
}

def get_search_corpus():
    """Build a corpus of strings for query correction suggestions."""
    title_list = list(Thesis.objects.values_list('title', flat=True))
    author_list = list(Thesis.objects.values_list('author', flat=True))
    keyword_list = [kw.strip() for kw in Thesis.objects.exclude(keywords__isnull=True).exclude(keywords__exact='').values_list('keywords', flat=True)]
    split_keywords = []
    for kw in keyword_list:
        split_keywords.extend([t.strip() for t in kw.split(',') if t.strip()])
    research_list = [rc.strip() for rc in Thesis.objects.exclude(research_category__isnull=True).exclude(research_category__exact='').values_list('research_category', flat=True)]
    split_research = []
    for rc in research_list:
        split_research.extend([t.strip() for t in rc.split(',') if t.strip()])
    dept_names = list(Department.objects.values_list('name', flat=True))
    course_names = list(Course.objects.values_list('name', flat=True))
    
    return [s for s in (title_list + author_list + split_keywords + split_research + dept_names + course_names) if s]

def get_lemmatized_tokens(query):
    """Tokenize and optionally lemmatize the query."""
    tokens = [t.lower() for t in re.findall(r"\w+", query) if t.strip()]
    search_tokens = [t for t in tokens if t not in STOPWORDS or len(t) > 3]
    if not search_tokens and tokens:
        search_tokens = tokens
    return search_tokens

def apply_search_scoring(queryset, query):
    """Apply scoring annotation to the queryset based on the query."""
    if not query:
        return queryset.annotate(score=Value(0, output_field=IntegerField()))
    
    # Phrase matching
    queryset = queryset.annotate(
        coauthor_json_text=Concat(
            F('co_authors__first_name'), Value(' '), F('co_authors__last_name'), 
            output_field=CharField()
        )
    )
    
    phrase_score = (
        Case(When(title__icontains=query, then=Value(PHRASE_WEIGHTS['title'])), default=Value(0), output_field=IntegerField()) +
        Case(When(abstract__icontains=query, then=Value(PHRASE_WEIGHTS['abstract'])), default=Value(0), output_field=IntegerField()) +
        Case(When(author__icontains=query, then=Value(PHRASE_WEIGHTS['author'])), default=Value(0), output_field=IntegerField()) +
        Case(When(keywords__icontains=query, then=Value(PHRASE_WEIGHTS['keywords'])), default=Value(0), output_field=IntegerField()) +
        Case(When(coauthor_json_text__icontains=query, then=Value(PHRASE_WEIGHTS['coauthor'])), default=Value(0), output_field=IntegerField()) +
        Case(When(department__name__icontains=query, then=Value(PHRASE_WEIGHTS['department'])), default=Value(0), output_field=IntegerField()) +
        Case(When(course__name__icontains=query, then=Value(PHRASE_WEIGHTS['course'])), default=Value(0), output_field=IntegerField())
    )
    
    # Token matching
    search_tokens = get_lemmatized_tokens(query)
    token_score_expr = Value(0)
    
    try:
        from .nlp_utils import get_lemmas
    except (ImportError, Exception):
        def get_lemmas(w): return {w}
        
    for token in search_tokens:
        lemmas = get_lemmas(token)
        title_q = Q(); author_q = Q(); abstract_q = Q(); keywords_q = Q()
        research_cat_q = Q(); cat_name_q = Q(); dept_name_q = Q(); course_name_q = Q()
        coauthor_q = Q()
        
        for lemma in lemmas:
            title_q |= Q(title__icontains=lemma); author_q |= Q(author__icontains=lemma)
            abstract_q |= Q(abstract__icontains=lemma); keywords_q |= Q(keywords__icontains=lemma)
            research_cat_q |= Q(research_category__icontains=lemma)
            cat_name_q |= Q(category__name__icontains=lemma)
            dept_name_q |= Q(department__name__icontains=lemma)
            course_name_q |= Q(course__name__icontains=lemma)
            coauthor_q |= Q(coauthor_json_text__icontains=lemma)
        
        token_score = (
            Case(When(title_q, then=Value(TOKEN_WEIGHTS['title'])), default=Value(0), output_field=IntegerField()) +
            Case(When(author_q, then=Value(TOKEN_WEIGHTS['author'])), default=Value(0), output_field=IntegerField()) +
            Case(When(coauthor_q, then=Value(TOKEN_WEIGHTS['coauthor'])), default=Value(0), output_field=IntegerField()) +
            Case(When(abstract_q, then=Value(TOKEN_WEIGHTS['abstract'])), default=Value(0), output_field=IntegerField()) +
            Case(When(keywords_q, then=Value(TOKEN_WEIGHTS['keywords'])), default=Value(0), output_field=IntegerField()) +
            Case(When(research_cat_q, then=Value(TOKEN_WEIGHTS['research_cat'])), default=Value(0), output_field=IntegerField()) +
            Case(When(cat_name_q, then=Value(TOKEN_WEIGHTS['cat_name'])), default=Value(0), output_field=IntegerField()) +
            Case(When(dept_name_q, then=Value(TOKEN_WEIGHTS['dept_name'])), default=Value(0), output_field=IntegerField()) +
            Case(When(course_name_q, then=Value(TOKEN_WEIGHTS['course_name'])), default=Value(0), output_field=IntegerField())
        )
        try:
            year_int = int(token)
            if 1900 < year_int < 2100:
                token_score += Case(When(year=year_int, then=Value(TOKEN_WEIGHTS['year'])), default=Value(0), output_field=IntegerField())
        except: pass
        token_score_expr += token_score
    
    return queryset.annotate(score=ExpressionWrapper(phrase_score + token_score_expr, output_field=IntegerField()))

def run_deep_search(queryset, query, base_order):
    """Execute deep search on the given queryset, searching inside PDF contents."""
    indexed_theses = queryset.exclude(full_text__isnull=True).exclude(full_text__exact='').filter(full_text__icontains=query)
    legacy_theses = queryset.filter(Q(full_text__isnull=True) | Q(full_text__exact=''))
    
    # Sort both sets by score and then base order
    indexed_theses = indexed_theses.order_by('-score', *base_order)
    legacy_theses = legacy_theses.order_by('-score', *base_order)
    
    final_matched_list = []
    seen_ids = set()
    
    # Search in already indexed text
    for t in indexed_theses:
        if t.id not in seen_ids:
            res = pdf_search_engine.search_in_extracted_text(t.full_text, query)
            if res.get('found'):
                t.deep_search_results = res
                t.deep_search_query = query
                final_matched_list.append(t)
                seen_ids.add(t.id)
    
    # Search in non-indexed PDFs (legacy)
    for t in legacy_theses:
        if t.id not in seen_ids and t.file:
            res = search_in_thesis_pdf(t, query)
            if res.get('found'):
                t.deep_search_results = res
                t.deep_search_query = query
                final_matched_list.append(t)
                seen_ids.add(t.id)
                
    return final_matched_list

def perform_thesis_search(
    query='', 
    mode='normal', 
    filters=None, 
    sort='date-desc'
):
    """
    Unified search entry point for Thesis model.
    Returns: (results, did_you_mean)
    """
    filters = filters or {}
    theses = Thesis.objects.filter(is_archived=False)
    did_you_mean = None
    
    # 1. Handle Query Suggestion
    if query:
        try:
            corpus = get_search_corpus()
            suggestion, confidence = suggest_query_correction(query, corpus)
            if suggestion and suggestion.strip().lower() != query.strip().lower():
                did_you_mean = suggestion
        except Exception:
            pass

    # 2. Apply Scoring
    theses = apply_search_scoring(theses, query)
    
    # 3. Apply Mode Filtering
    if query and mode != 'deep':
        theses = theses.filter(score__gt=0)
        
    # 4. Handle Sorting logic
    sort_options = {
        'date-asc': ('year', 'title'),
        'date-desc': ('-year', 'title'),
        'title-asc': ('title',),
        'title-desc': ('-title',),
        'author-asc': ('author', 'title'),
        'author-desc': ('-author', 'title')
    }
    base_order = sort_options.get(sort, ('-year', 'title'))
    
    if query:
        # If sorted by relevance primarily
        sort_map = {
            'date-asc': ('year', '-score'), 'date-desc': ('-year', '-score'),
            'title-asc': ('title', '-score'), 'title-desc': ('-title', '-score'),
            'author-asc': ('author', '-score'), 'author-desc': ('-author', '-score')
        }
        order_by = sort_map.get(sort, ('-score', '-year'))
    else:
        order_by = base_order
        
    theses = theses.order_by(*order_by)
    
    # 5. Apply Business Filters
    if filters.get('years'):
        theses = theses.filter(year__in=filters['years'])
    if filters.get('descriptors'):
        theses = theses.filter(category__name__in=filters['descriptors'])
    if filters.get('authors'):
        theses = theses.filter(author__in=filters['authors'])
    if filters.get('types'):
        theses = theses.filter(thesis_type__in=filters['types'])
    if filters.get('department') and filters['department'] != 'all':
        theses = theses.filter(department__id=filters['department'])
    if filters.get('courses'):
        theses = theses.filter(course__id__in=filters['courses'])
    if filters.get('category_obj'):
        theses = theses.filter(category=filters['category_obj'])

    # 6. Handle Deep Search and Serialization
    if query and mode == 'deep':
        theses = run_deep_search(theses, query, base_order)
    else:
        # Standard uniqueness check for annotated results
        unique_results = []
        seen_ids = set()
        for t in theses:
            if t.id not in seen_ids:
                unique_results.append(t)
                seen_ids.add(t.id)
        theses = unique_results

    # Post-processing helper tagging
    for thesis in theses:
        thesis.keywords_list = [k.strip() for k in (thesis.keywords or "").split(',') if k.strip()]
        thesis.research_categories_list = [c.strip() for c in (thesis.research_category or "").split(',') if c.strip()]
        if not hasattr(thesis, 'deep_search_results'):
            thesis.deep_search_results = None

    return theses, did_you_mean
