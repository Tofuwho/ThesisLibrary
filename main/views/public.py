import re
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q, F, Value, IntegerField, Case, When, ExpressionWrapper, CharField
from django.db.models.functions import Concat
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404

from ..models import Thesis, Category, Department, Course
from authapp.models import Profile
from ..utils import suggest_query_correction, get_thesis_preview, search_in_thesis_pdf

# ----------------------
# Pages / Landing
# ----------------------
def landing_page(request):
    return render(request, 'main/landing.html')

def about_page(request):
    return render(request, 'main/about.html')

@login_required
def index_page(request):
    recent_theses = Thesis.objects.order_by('-id')[:6]
    departments = Department.objects.all().order_by('name')[:8]
    return render(request, 'main/index.html', {
        'recent_theses': recent_theses,
        'departments': departments,
    })

@login_required
def categories_page(request):
    theses = Thesis.objects.all()
    search_query = request.GET.get('search') or ''
    
    can_full_view = request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role in [Profile.ADMIN, Profile.LIBRARIAN]
    
    search_mode = request.GET.get('search_mode', 'normal')
    if search_mode == 'deep' and not can_full_view:
        search_mode = 'normal'
        messages.warning(request, "Deep search (searching inside PDF contents) is restricted to Administrators and Librarians.")
    selected_years = request.GET.getlist('year')
    selected_descriptors = request.GET.getlist('descriptor')
    selected_authors = request.GET.getlist('author')
    selected_types = request.GET.getlist('type')
    sort = request.GET.get('sort') or 'date-desc'
    selected_department = request.GET.get('department')
    selected_courses = request.GET.getlist('course')

    did_you_mean = None
    effective_query = search_query
    if search_query:
        try:
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

            corpus = [s for s in (title_list + author_list + split_keywords + split_research + dept_names + course_names) if s]

            suggestion, confidence = suggest_query_correction(search_query, corpus)
            if suggestion and suggestion.strip().lower() != search_query.strip().lower():
                did_you_mean = suggestion
        except Exception:
            did_you_mean = None

    if search_query:
        STOPWORDS = {
            'a', 'an', 'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'as', 
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 
            'did', 'but', 'if', 'then', 'else', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 
            'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 
            'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 
            'should', 'now', 'thesis', 'study', 'research', 'library'
        }
        
        theses = theses.annotate(
            coauthor_json_text=Concat(
                F('co_authors__first_name'), Value(' '), F('co_authors__last_name'), 
                output_field=CharField()
            )
        )
        
        phrase_score = (
            Case(When(title__icontains=search_query, then=Value(150)), default=Value(0), output_field=IntegerField()) +
            Case(When(abstract__icontains=search_query, then=Value(100)), default=Value(0), output_field=IntegerField()) +
            Case(When(author__icontains=search_query, then=Value(80)), default=Value(0), output_field=IntegerField()) +
            Case(When(keywords__icontains=search_query, then=Value(80)), default=Value(0), output_field=IntegerField()) +
            Case(When(coauthor_json_text__icontains=search_query, then=Value(70)), default=Value(0), output_field=IntegerField()) +
            Case(When(department__name__icontains=search_query, then=Value(50)), default=Value(0), output_field=IntegerField()) +
            Case(When(course__name__icontains=search_query, then=Value(40)), default=Value(0), output_field=IntegerField())
        )
        
        tokens = [t.lower() for t in re.findall(r"\w+", search_query) if t.strip()]
        search_tokens = [t for t in tokens if t not in STOPWORDS or len(t) > 3]
        if not search_tokens and tokens: search_tokens = tokens
        
        token_score_expr = Value(0)
        try:
            from ..nlp_utils import get_lemmas
        except Exception:
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
                Case(When(title_q, then=Value(30)), default=Value(0), output_field=IntegerField()) +
                Case(When(author_q, then=Value(15)), default=Value(0), output_field=IntegerField()) +
                Case(When(coauthor_q, then=Value(15)), default=Value(0), output_field=IntegerField()) +
                Case(When(abstract_q, then=Value(10)), default=Value(0), output_field=IntegerField()) +
                Case(When(keywords_q, then=Value(10)), default=Value(0), output_field=IntegerField()) +
                Case(When(research_cat_q, then=Value(5)), default=Value(0), output_field=IntegerField()) +
                Case(When(cat_name_q, then=Value(5)), default=Value(0), output_field=IntegerField()) +
                Case(When(dept_name_q, then=Value(5)), default=Value(0), output_field=IntegerField()) +
                Case(When(course_name_q, then=Value(5)), default=Value(0), output_field=IntegerField())
            )
            try:
                year_int = int(token)
                if 1900 < year_int < 2100:
                    token_score += Case(When(year=year_int, then=Value(20)), default=Value(0), output_field=IntegerField())
            except: pass
            token_score_expr += token_score
        
        theses = theses.annotate(score=ExpressionWrapper(phrase_score + token_score_expr, output_field=IntegerField()))
        
        if search_mode != 'deep':
            theses = theses.filter(score__gt=0)
            
        if not sort or sort == 'date-desc':
            theses = theses.order_by('-score', '-year')
        else:
            sort_map = {
                'date-asc': ('year', '-score'), 'date-desc': ('-year', '-score'),
                'title-asc': ('title', '-score'), 'title-desc': ('-title', '-score'),
                'author-asc': ('author', '-score'), 'author-desc': ('-author', '-score')
            }
            theses = theses.order_by(*sort_map.get(sort, ('-score', '-year')))

    if selected_years:
        numeric_years = [int(y) for y in selected_years if str(y).isdigit()]
        if numeric_years:
            theses = theses.filter(year__in=numeric_years)

    if selected_descriptors:
        theses = theses.filter(category__name__in=selected_descriptors)

    if selected_authors:
        theses = theses.filter(author__in=selected_authors)

    if selected_types:
        theses = theses.filter(thesis_type__in=selected_types)

    if selected_department and selected_department != 'all':
        try:
            dept_id = int(selected_department)
            theses = theses.filter(department__id=dept_id)
        except ValueError:
            pass

    if selected_courses:
        try:
            course_ids = [int(cid) for cid in selected_courses if cid.isdigit()]
            if course_ids:
                theses = theses.filter(course__id__in=course_ids)
        except ValueError:
            pass

    if search_query and search_mode == 'deep':
        try:
            sample_theses = list(theses[:50])
            pdf_tokens = []
            for t in sample_theses:
                if not getattr(t, 'file', None):
                    continue
                preview_text = get_thesis_preview(t, max_pages=2) or ''
                pdf_tokens.extend([w for w in re.findall(r"\w+", preview_text) if w])
            suggestion_pdf, conf_pdf = suggest_query_correction(search_query, pdf_tokens)
            if suggestion_pdf and suggestion_pdf.strip().lower() != search_query.strip().lower():
                did_you_mean = suggestion_pdf
        except Exception:
            pass

    sort_options = {
        'date-asc': ('year', 'title'),
        'date-desc': ('-year', 'title'),
        'title-asc': ('title',),
        'title-desc': ('-title',),
        'author-asc': ('author', 'title'),
        'author-desc': ('-author', 'title')
    }
    base_order = sort_options.get(sort, ('-year', 'title'))

    if search_query and search_mode == 'deep':
        from ..utils import pdf_search_engine
        indexed_theses = theses.exclude(full_text__isnull=True).exclude(full_text__exact='').filter(full_text__icontains=effective_query)
        legacy_theses = theses.filter(Q(full_text__isnull=True) | Q(full_text__exact=''))
        
        if search_query:
            indexed_theses = indexed_theses.order_by('-score', *base_order)
            legacy_theses = legacy_theses.order_by('-score', *base_order)
        else:
            indexed_theses = indexed_theses.order_by(*base_order)
            legacy_theses = legacy_theses.order_by(*base_order)
            
        final_matched_list = []
        seen_ids = set()
        
        for t in indexed_theses:
            if t.id not in seen_ids:
                res = pdf_search_engine.search_in_extracted_text(t.full_text, effective_query)
                if res.get('found'):
                    t.deep_search_results = res
                    t.deep_search_query = effective_query
                    final_matched_list.append(t)
                    seen_ids.add(t.id)
        
        for t in legacy_theses:
            if t.id not in seen_ids and t.file:
                res = search_in_thesis_pdf(t, effective_query)
                if res.get('found'):
                    t.deep_search_results = res
                    t.deep_search_query = effective_query
                    final_matched_list.append(t)
                    seen_ids.add(t.id) if t.id else None
        
        theses = final_matched_list
    else:
        if search_query:
            theses = theses.order_by('-score', *base_order)
        else:
            theses = theses.order_by(*base_order)
            
        unique_results = []
        seen_ids = set()
        for t in theses:
            if t.id not in seen_ids:
                unique_results.append(t)
                seen_ids.add(t.id)
        theses = unique_results

    for thesis in theses:
        thesis.keywords_list = [k.strip() for k in (thesis.keywords or "").split(',') if k.strip()]
        thesis.research_categories_list = [c.strip() for c in (thesis.research_category or "").split(',') if c.strip()]
        if not getattr(thesis, 'deep_search_results', None):
            thesis.deep_search_results = None

    departments = Department.objects.all().order_by('name')
    if selected_department and selected_department != 'all':
        try:
            dept_id = int(selected_department)
            courses = Course.objects.filter(department__id=dept_id).order_by('name')
        except ValueError:
            courses = Course.objects.none()
    else:
        courses = Course.objects.none()

    years = Thesis.objects.values('year').annotate(count=Count('id')).order_by('-year')
    categories = Category.objects.annotate(count=Count('thesis')).order_by('name')
    authors = Thesis.objects.values('author').annotate(count=Count('id')).order_by('author')
    types = Thesis.objects.exclude(thesis_type__isnull=True).exclude(thesis_type__exact='')\
                          .values('thesis_type').annotate(count=Count('id')).order_by('thesis_type')

    total_results = len(theses) if isinstance(theses, list) else theses.count()

    page_number = request.GET.get('page') or 1
    paginator = Paginator(theses, 16)
    page_obj = paginator.get_page(page_number)

    context = {
        'theses': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'years': [{'year': y['year'], 'count': y['count']} for y in years],
        'authors': [{'name': a['author'], 'count': a['count']} for a in authors],
        'types': [{'name': t['thesis_type'], 'count': t['count']} for t in types],
        'total_results': total_results,
        'current_sort': sort,
        'selected_department': selected_department,
        'selected_courses': selected_courses,
        'departments': departments,
        'courses': courses,
        'search_mode': search_mode,
        'did_you_mean': did_you_mean,
        'effective_query': effective_query,
        'can_full_view': can_full_view,
    }
    return render(request, 'main/categories.html', context)

@login_required
def category_detail(request, category_name):
    """Browse theses by specific category"""
    category = Category.objects.filter(name__iexact=category_name).first()
    if not category:
        category = Category.objects.filter(name__icontains=category_name).first()
    if not category:
        raise Http404(f"Category '{category_name}' not found")

    theses = Thesis.objects.filter(category=category)
    search_query = request.GET.get('search') or ''
    selected_years = request.GET.getlist('year')
    selected_authors = request.GET.getlist('author')
    selected_types = request.GET.getlist('type')
    sort = request.GET.get('sort') or 'date-desc'

    if search_query:
        STOPWORDS = {
            'a', 'an', 'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'as', 
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 
            'did', 'but', 'if', 'then', 'else', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 
            'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 
            'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 
            'should', 'now', 'thesis', 'study', 'research', 'library'
        }
        
        theses = theses.annotate(
            coauthor_json_text=Concat(
                F('co_authors__first_name'), Value(' '), F('co_authors__last_name'), 
                output_field=CharField()
            )
        )
        
        phrase_score = (
            Case(When(title__icontains=search_query, then=Value(150)), default=Value(0), output_field=IntegerField()) +
            Case(When(abstract__icontains=search_query, then=Value(100)), default=Value(0), output_field=IntegerField()) +
            Case(When(author__icontains=search_query, then=Value(80)), default=Value(0), output_field=IntegerField()) +
            Case(When(keywords__icontains=search_query, then=Value(80)), default=Value(0), output_field=IntegerField()) +
            Case(When(coauthor_json_text__icontains=search_query, then=Value(70)), default=Value(0), output_field=IntegerField()) +
            Case(When(department__name__icontains=search_query, then=Value(50)), default=Value(0), output_field=IntegerField()) +
            Case(When(course__name__icontains=search_query, then=Value(40)), default=Value(0), output_field=IntegerField())
        )
        
        tokens = [t.lower() for t in re.findall(r"\w+", search_query) if t.strip()]
        search_tokens = [t for t in tokens if t not in STOPWORDS or len(t) > 3]
        if not search_tokens and tokens: search_tokens = tokens
        
        token_score_expr = Value(0)
        try:
            from ..nlp_utils import get_lemmas
        except Exception:
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
                Case(When(title_q, then=Value(30)), default=Value(0), output_field=IntegerField()) +
                Case(When(author_q, then=Value(15)), default=Value(0), output_field=IntegerField()) +
                Case(When(coauthor_q, then=Value(15)), default=Value(0), output_field=IntegerField()) +
                Case(When(abstract_q, then=Value(10)), default=Value(0), output_field=IntegerField()) +
                Case(When(keywords_q, then=Value(10)), default=Value(0), output_field=IntegerField()) +
                Case(When(research_cat_q, then=Value(5)), default=Value(0), output_field=IntegerField()) +
                Case(When(cat_name_q, then=Value(5)), default=Value(0), output_field=IntegerField()) +
                Case(When(dept_name_q, then=Value(5)), default=Value(0), output_field=IntegerField()) +
                Case(When(course_name_q, then=Value(5)), default=Value(0), output_field=IntegerField())
            )
            try:
                year_int = int(token)
                if 1900 < year_int < 2100:
                    token_score += Case(When(year=year_int, then=Value(20)), default=Value(0), output_field=IntegerField())
            except: pass
            token_score_expr += token_score
            
        theses = theses.annotate(score=ExpressionWrapper(phrase_score + token_score_expr, output_field=IntegerField())).filter(score__gt=0)

    if selected_years:
        numeric_years = [int(y) for y in selected_years if str(y).isdigit()]
        if numeric_years:
            theses = theses.filter(year__in=numeric_years)

    if selected_authors:
        theses = theses.filter(author__in=selected_authors)

    if selected_types:
        theses = theses.filter(thesis_type__in=selected_types)

    sort_options = {
        'date-asc': ('year', 'title'),
        'date-desc': ('-year', 'title'),
        'title-asc': ('title',),
        'title-desc': ('-title',),
        'author-asc': ('author', 'title'),
        'author-desc': ('-author', 'title')
    }
    base_order = sort_options.get(sort, ('-year', 'title'))
    if search_query:
        if not sort or sort == 'date-desc':
            theses = theses.order_by('-score', '-year')
        else:
            sort_map = {
                'date-asc': ('year', '-score'), 'date-desc': ('-year', '-score'),
                'title-asc': ('title', '-score'), 'title-desc': ('-title', '-score'),
                'author-asc': ('author', '-score'), 'author-desc': ('-author', '-score')
            }
            theses = theses.order_by(*sort_map.get(sort, ('-score', '-year')))
    else:
        theses = theses.order_by(*base_order)
        
    unique_theses = []
    seen = set()
    for t in theses:
        if t.id not in seen:
            seen.add(t.id)
            unique_theses.append(t)
    theses = unique_theses

    years = Thesis.objects.filter(category=category).values('year').annotate(count=Count('id')).order_by('-year')
    authors = Thesis.objects.filter(category=category).values('author').annotate(count=Count('id')).order_by('author')
    types = Thesis.objects.filter(category=category).exclude(thesis_type__isnull=True)\
                          .exclude(thesis_type__exact='').values('thesis_type')\
                          .annotate(count=Count('id')).order_by('thesis_type')

    total_results = len(theses)
    context = {
        'category': category,
        'theses': theses,
        'years': [{'year': y['year'], 'count': y['count']} for y in years],
        'authors': [{'name': a['author'], 'count': a['count']} for a in authors],
        'types': [{'name': t['thesis_type'], 'count': t['count']} for t in types],
        'total_results': total_results,
        'current_sort': sort,
    }
    return render(request, 'main/category_detail.html', context)

@login_required
def thesis_detail(request, pk: int):
    from ..models import Submission
    thesis = get_object_or_404(Thesis, pk=pk)
    is_authenticated = request.user.is_authenticated
    
    can_view_full = False
    if is_authenticated:
        can_view_full = request.user.profile.role in [Profile.ADMIN, Profile.LIBRARIAN]
        
    return render(request, 'main/thesis_detail.html', {
        'thesis': thesis,
        'is_authenticated': is_authenticated,
        'can_view_full': can_view_full
    })
