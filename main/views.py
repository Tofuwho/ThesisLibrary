
# Create your views here.
from django.shortcuts import render
from .models import Thesis, Category

def landing_page(request):
    return render(request, 'main/landing.html')

def about_page(request):
    return render(request, 'main/about.html')

def index_page(request):
    return render(request, 'main/index.html')

def categories_page(request):
    # Dummy theses
    theses = [
        {
            'title': 'Smart Traffic System',
            'author': 'Alice Reyes',
            'year': 2025,
            'abstract': 'This thesis explores smart traffic optimization using AI...',
            'specialization': 'Computer Science',
            'thesis_type': 'Capstone'
        },
        {
            'title': 'E-Governance via Blockchain',
            'author': 'Mark Cruz',
            'year': 2023,
            'abstract': 'An application of blockchain for secure online governance...',
            'specialization': 'Information Systems',
            'thesis_type': 'Thesis'
        },
    ]

    # Dummy filter data
    categories = [
        {'name': 'AI'},
        {'name': 'Blockchain'},
        {'name': 'Mobile Apps'},
    ]

    # Dummy years for publication filter
    years = [2025, 2024, 2023, 2022, 2021]

    return render(request, 'main/categories.html', {
        'theses': theses,
        'categories': categories,
        'years': years,
        'total_results': len(theses),
    })

def student_dashboard(request):
    return render(request, 'main/student_dashboard.html')