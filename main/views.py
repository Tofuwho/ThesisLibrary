from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Q
from .models import Thesis, Category
from django.http import FileResponse, Http404
import os

def landing_page(request):
    return render(request, 'main/landing.html')

def about_page(request):
    return render(request, 'main/about.html')

def index_page(request):
    recent_theses = Thesis.objects.order_by('-id')[:6]
    categories = Category.objects.all()[:6]
    return render(request, 'main/index.html', {
        'recent_theses': recent_theses,
        'categories': categories,
    })

def categories_page(request):
    theses = Thesis.objects.all()

    search_query = request.GET.get('search') or ''
    selected_years = request.GET.getlist('year')
    selected_descriptors = request.GET.getlist('descriptor')
    selected_authors = request.GET.getlist('author')
    selected_types = request.GET.getlist('type')
    sort = request.GET.get('sort') or 'date-desc'

    if search_query:
        theses = theses.filter(
            Q(title__icontains=search_query)
            | Q(author__icontains=search_query)
            | Q(abstract__icontains=search_query)
        )

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

    # Sorting
    if sort == 'date-asc':
        theses = theses.order_by('year', 'title')
    elif sort == 'title-asc':
        theses = theses.order_by('title')
    elif sort == 'title-desc':
        theses = theses.order_by('-title')
    else:  # date-desc
        theses = theses.order_by('-year', 'title')

    theses = theses.distinct()

    # Sidebar data with counts
    years = (
        Thesis.objects.values('year')
        .annotate(count=Count('id'))
        .order_by('-year')
    )
    categories = Category.objects.annotate(count=Count('thesis')).order_by('name')
    authors = (
        Thesis.objects.values(name=Count('author'))
    )
    # Proper authors aggregation (name + count)
    authors = (
        Thesis.objects.values('author')
        .annotate(count=Count('id'))
        .order_by('author')
    )
    types = (
        Thesis.objects.values(name_field=Count('thesis_type'))
    )
    types = (
        Thesis.objects.values('thesis_type')
        .annotate(count=Count('id'))
        .order_by('thesis_type')
    )

    total_results = theses.count()

    context = {
        'theses': theses,
        'categories': categories,
        'years': [y['year'] for y in years],
        'authors': [
            {'name': a['author'], 'count': a['count']} for a in authors
        ],
        'types': [
            {'name': t['thesis_type'], 'count': t['count']} for t in types
        ],
        'total_results': total_results,
    }
    return render(request, 'main/categories.html', context)

def student_dashboard(request):
    return render(request, 'main/student_dashboard.html')


def thesis_detail(request, pk: int):
    thesis = get_object_or_404(Thesis, pk=pk)
    return render(request, 'main/thesis_detail.html', {'thesis': thesis})

def view_thesis_file(request, pk):
    thesis = get_object_or_404(Thesis, pk=pk)
    if not thesis.file:
        raise Http404('File not found.')
    response = FileResponse(thesis.file.open('rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(thesis.file.name)}"'
    return response

def download_thesis_file(request, pk):
    thesis = get_object_or_404(Thesis, pk=pk)
    if not thesis.file:
        raise Http404('File not found.')
    response = FileResponse(thesis.file.open('rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(thesis.file.name)}"'
    return response