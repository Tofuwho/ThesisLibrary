from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

def landing_page(request):
    return render(request, 'main/landing.html')

def about_page(request):
    return render(request, 'main/about.html')

def index_page(request):
    return render(request, 'main/index.html')

def categories_page(request):
    return render(request, 'main/categories.html')

def student_dashboard(request):
    return render(request, 'main/student_dashboard.html')