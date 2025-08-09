from django.shortcuts import render, get_object_or_404
from library.models import Thesis, Category

# Create your views here.
from django.shortcuts import render

def landing_page(request):
    return render(request, 'main/landing.html')

def about_page(request):
    return render(request, 'main/about.html')

def index_page(request):
    recent_theses = Thesis.objects.order_by('-created_at')[:6]
    categories = Category.objects.all()[:6]
    return render(request, 'main/index.html', {
        'recent_theses': recent_theses,
        'categories': categories,
    })

def categories_page(request):
    theses = Thesis.objects.all()
    categories = Category.objects.all()

    search_query = request.GET.get('search') or ''
    selected_year = request.GET.get('year') or ''
    selected_descriptor = request.GET.get('descriptor') or ''
    sort = request.GET.get('sort') or 'date-desc'

    if search_query:
        theses = theses.filter(title__icontains=search_query) | theses.filter(author__icontains=search_query) | theses.filter(abstract__icontains=search_query)

    if selected_year:
        try:
            theses = theses.filter(year=int(selected_year))
        except ValueError:
            pass

    if selected_descriptor:
        theses = theses.filter(categories__name=selected_descriptor)

    if sort == 'date-asc':
        theses = theses.order_by('year', 'title')
    elif sort == 'title-asc':
        theses = theses.order_by('title')
    elif sort == 'title-desc':
        theses = theses.order_by('-title')
    else:  # date-desc
        theses = theses.order_by('-year', 'title')

    years = Thesis.objects.order_by('-year').values_list('year', flat=True).distinct()
    total_results = theses.count()

    context = {
        'theses': theses,
        'categories': categories,
        'years': years,
        'total_results': total_results,
    }
    return render(request, 'main/categories.html', context)

def student_dashboard(request):
    return render(request, 'main/student_dashboard.html')


def thesis_detail(request, pk: int):
    thesis = get_object_or_404(Thesis, pk=pk)
    return render(request, 'main/thesis_detail.html', {'thesis': thesis})