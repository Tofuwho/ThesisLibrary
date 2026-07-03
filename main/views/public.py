import re
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404

from ..models import Thesis, Category, Department, Course, Submission
from authapp.models import Profile
from ..search_utils import perform_thesis_search

# ----------------------
# Pages / Landing
# ----------------------
def landing_page(request):
    return render(request, 'main/landing.html')

def about_page(request):
    return render(request, 'main/about.html')

@login_required
def index_page(request):
    recent_theses = Thesis.objects.filter(is_archived=False).order_by('-id')[:6]
    departments = Department.objects.all().order_by('name')[:8]
    
    # Calculate live stats
    total_theses_count = Thesis.objects.filter(is_archived=False).count()
    total_theses = f"{total_theses_count:,}"
    total_colleges = Department.objects.count()
    
    total_submissions_count = Submission.objects.count()
    total_submissions = f"{total_submissions_count:,}"
    
    if total_theses_count > 0:
        open_access_count = Thesis.objects.filter(is_archived=False).exclude(file='').exclude(file__isnull=True).count()
        open_access_percent = int((open_access_count / total_theses_count) * 100)
    else:
        open_access_percent = 100

    return render(request, 'main/index.html', {
        'recent_theses': recent_theses,
        'departments': departments,
        'total_submissions': total_submissions,
        'total_theses': total_theses,
        'total_colleges': total_colleges,
        'open_access_percent': open_access_percent,
    })

@login_required
def categories_page(request):
    search_query = request.GET.get('search') or ''
    can_full_view = request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role in [Profile.ADMIN, Profile.LIBRARIAN]
    
    search_mode = request.GET.get('search_mode', 'normal')
    if search_mode == 'deep' and not can_full_view:
        search_mode = 'normal'
        messages.warning(request, "Deep search is restricted to Administrators and Librarians.")
        
    sort = request.GET.get('sort') or 'date-desc'
    filters = {
        'years': [int(y) for y in request.GET.getlist('year') if y.isdigit()],
        'descriptors': request.GET.getlist('category') or request.GET.getlist('descriptor'),
        'authors': request.GET.getlist('author'),
        'types': request.GET.getlist('type'),
        'department': request.GET.get('department'),
        'courses': [int(c) for c in request.GET.getlist('course') if c.isdigit()],
        'research_categories': request.GET.getlist('research_category'),
        'specializations': request.GET.getlist('specialization'),
        'supervisors': request.GET.getlist('supervisor')
    }

    theses, did_you_mean = perform_thesis_search(
        query=search_query,
        mode=search_mode,
        filters=filters,
        sort=sort
    )

    departments = Department.objects.all().order_by('name')
    if filters['department'] and filters['department'] != 'all':
        try:
            dept_id = int(filters['department'])
            courses = Course.objects.filter(department__id=dept_id).order_by('name')
        except (ValueError, TypeError):
            courses = Course.objects.none()
    else:
        courses = Course.objects.none()

    # Retrieve unique filtering options and active counts
    years = Thesis.objects.filter(is_archived=False).values('year').annotate(count=Count('id')).order_by('-year')
    categories = Category.objects.all().annotate(count=Count('thesis', filter=Q(thesis__is_archived=False))).order_by('name')
    authors = Thesis.objects.filter(is_archived=False).values('author').annotate(count=Count('id')).order_by('author')
    types = Thesis.objects.filter(is_archived=False).exclude(thesis_type__isnull=True).exclude(thesis_type__exact='')\
                          .values('thesis_type').annotate(count=Count('id')).order_by('thesis_type')

    # Research Categories (comma-separated extraction)
    raw_research_cats = Thesis.objects.filter(is_archived=False).exclude(research_category__isnull=True)\
                                      .exclude(research_category__exact='').values_list('research_category', flat=True).distinct()
    research_cats_set = set()
    for rc in raw_research_cats:
        for val in rc.split(','):
            val_clean = val.strip()
            if val_clean:
                research_cats_set.add(val_clean)
    
    research_categories_list = []
    for rc in sorted(research_cats_set):
        count = Thesis.objects.filter(research_category__icontains=rc, is_archived=False).count()
        research_categories_list.append({'name': rc, 'count': count})

    # Specializations
    specializations = Thesis.objects.filter(is_archived=False).exclude(specialization__isnull=True).exclude(specialization__exact='')\
                                    .values('specialization').annotate(count=Count('id')).order_by('specialization')

    # Supervisors
    supervisors = Thesis.objects.filter(is_archived=False).exclude(supervisor_name__isnull=True).exclude(supervisor_name__exact='')\
                                .values('supervisor_name').annotate(count=Count('id')).order_by('supervisor_name')

    total_results = len(theses)
    page_number = request.GET.get('page') or 1
    paginator = Paginator(theses, 6)
    page_obj = paginator.get_page(page_number)

    context = {
        'theses': page_obj,
        'page_obj': page_obj,
        'categories': categories,
        'years': [{'year': y['year'], 'count': y['count']} for y in years],
        'authors': [{'name': a['author'], 'count': a['count']} for a in authors],
        'types': [{'name': t['thesis_type'], 'count': t['count']} for t in types],
        'research_categories': research_categories_list,
        'specializations': [{'name': s['specialization'], 'count': s['count']} for s in specializations],
        'supervisors': [{'name': sup['supervisor_name'], 'count': sup['count']} for sup in supervisors],
        'total_results': total_results,
        'current_sort': sort,
        'selected_department': filters['department'],
        'selected_courses': filters['courses'],
        'departments': departments,
        'courses': courses,
        'search_mode': search_mode,
        'did_you_mean': did_you_mean,
        'effective_query': search_query,
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

    search_query = request.GET.get('search') or ''
    sort = request.GET.get('sort') or 'date-desc'
    filters = {
        'years': [int(y) for y in request.GET.getlist('year') if y.isdigit()],
        'authors': request.GET.getlist('author'),
        'types': request.GET.getlist('type'),
        'category_obj': category
    }

    theses, did_you_mean = perform_thesis_search(
        query=search_query,
        filters=filters,
        sort=sort
    )

    years = Thesis.objects.filter(category=category).values('year').annotate(count=Count('id')).order_by('-year')
    authors = Thesis.objects.filter(category=category).values('author').annotate(count=Count('id')).order_by('author')
    types = Thesis.objects.filter(category=category).exclude(thesis_type__isnull=True)\
                          .exclude(thesis_type__exact='').values('thesis_type')\
                          .annotate(count=Count('id')).order_by('thesis_type')

    context = {
        'category': category,
        'theses': theses,
        'years': [{'year': y['year'], 'count': y['count']} for y in years],
        'authors': [{'name': a['author'], 'count': a['count']} for a in authors],
        'types': [{'name': t['thesis_type'], 'count': t['count']} for t in types],
        'total_results': len(theses),
        'current_sort': sort,
        'did_you_mean': did_you_mean,
    }
    return render(request, 'main/category_detail.html', context)

def get_initials(name):
    if not name:
        return ""
    cleaned_name = re.sub(r'^(Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s+', '', name, flags=re.IGNORECASE)
    parts = cleaned_name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    elif len(parts) == 1:
        return parts[0][:2].upper()
    return ""

@login_required
def thesis_detail(request, pk: int):
    thesis = get_object_or_404(Thesis, pk=pk)
    is_authenticated = request.user.is_authenticated
    
    can_view_full = False
    if is_authenticated:
        can_view_full = request.user.profile.role in [Profile.ADMIN, Profile.LIBRARIAN]
        
    # Extra data for the new layout
    keywords_list = [k.strip() for k in (thesis.keywords or "").split(',') if k.strip()]
    
    coauthor_list = thesis.get_coauthor_names()
    coauthors_str = ""
    if coauthor_list:
        if len(coauthor_list) == 1:
            coauthors_str = coauthor_list[0]
        elif len(coauthor_list) == 2:
            coauthors_str = f"{coauthor_list[0]} and {coauthor_list[1]}"
        else:
            coauthors_str = ", ".join(coauthor_list[:-1]) + f", and {coauthor_list[-1]}"
            
    supervisor_initials = get_initials(thesis.supervisor_name)
    co_supervisor_initials = get_initials(thesis.co_supervisor_name)
    
    import os
    filename = os.path.basename(thesis.file.name) if thesis.file else "manuscript.pdf"
    
    restricted_page_count = 1
    if thesis.file:
        try:
            import fitz
            doc = fitz.open(thesis.file.path)
            original_page_count = doc.page_count
            doc.close()
            restricted_page_count = min(3, original_page_count)
        except Exception:
            try:
                from PyPDF2 import PdfReader
                pdf_reader = PdfReader(thesis.file.open('rb'))
                original_page_count = len(pdf_reader.pages)
                restricted_page_count = min(3, original_page_count)
            except Exception:
                restricted_page_count = 3
                
    return render(request, 'main/thesis_detail.html', {
        'thesis': thesis,
        'is_authenticated': is_authenticated,
        'can_view_full': can_view_full,
        'keywords_list': keywords_list,
        'coauthors': coauthors_str,
        'supervisor_initials': supervisor_initials,
        'co_supervisor_initials': co_supervisor_initials,
        'filename': filename,
        'restricted_page_count': restricted_page_count,
    })
