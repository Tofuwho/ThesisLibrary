from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required

from ..models import Category, Department, Course
from ..utils import extract_abstract_from_pdf, extract_title_from_pdf

@require_GET
def api_departments(request, category_id):
    try:
        category = Category.objects.get(id=category_id)
        return JsonResponse({'departments': [{'id': d.id, 'name': d.name} for d in category.departments.all().order_by('name')]})
    except: return JsonResponse({'error': 'Not found'}, status=404)

@require_GET
def api_courses(request, department_id):
    try:
        dept = Department.objects.get(id=department_id)
        return JsonResponse({'courses': [{'id': c.id, 'name': c.name} for c in dept.courses.all().order_by('name')]})
    except: return JsonResponse({'error': 'Not found'}, status=404)

@login_required
@require_POST
def api_extract_abstract(request):
    try:
        f = request.FILES.get('pdf_file')
        if not f or not f.name.endswith('.pdf'): return JsonResponse({'error': 'Invalid file'}, status=400)
        return JsonResponse({'success': True, 'abstract': extract_abstract_from_pdf(f), 'title': extract_title_from_pdf(f)})
    except Exception as e: return JsonResponse({'error': str(e)}, status=500)

def csrf_failure(request, reason=""):
    return render(request, "errors/csrf_failure.html", status=403)
