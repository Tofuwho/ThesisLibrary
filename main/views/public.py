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
    recent_theses = Thesis.objects.order_by('-id')[:6]
    departments = Department.objects.all().order_by('name')[:8]
    return render(request, 'main/index.html', {
        'recent_theses': recent_theses,
        'departments': departments,
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
        'descriptors': request.GET.getlist('descriptor'),
        'authors': request.GET.getlist('author'),
        'types': request.GET.getlist('type'),
        'department': request.GET.get('department'),
        'courses': [int(c) for c in request.GET.getlist('course') if c.isdigit()]
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

    years = Thesis.objects.values('year').annotate(count=Count('id')).order_by('-year')
    categories = Category.objects.annotate(count=Count('thesis')).order_by('name')
    authors = Thesis.objects.values('author').annotate(count=Count('id')).order_by('author')
    types = Thesis.objects.exclude(thesis_type__isnull=True).exclude(thesis_type__exact='')\
                          .values('thesis_type').annotate(count=Count('id')).order_by('thesis_type')

    total_results = len(theses)
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

@login_required
def thesis_detail(request, pk: int):
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
