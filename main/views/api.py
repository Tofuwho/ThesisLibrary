from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required

from ..models import Category, Department
from ..utils import extract_abstract_from_pdf, extract_title_from_pdf

@require_GET
def api_departments(request, category_id):
    try:
        category = Category.objects.get(id=category_id)
        return JsonResponse({'departments': [{'id': d.id, 'name': d.name} for d in category.departments.all().order_by('name')]})
    except Exception:
        return JsonResponse({'error': 'Not found'}, status=404)

@require_GET
def api_courses(request, department_id):
    try:
        dept = Department.objects.get(id=department_id)
        return JsonResponse({'courses': [{'id': c.id, 'name': c.name} for c in dept.courses.all().order_by('name')]})
    except Exception:
        return JsonResponse({'error': 'Not found'}, status=404)

@login_required
@require_POST
def api_extract_abstract(request):
    try:
        f = request.FILES.get('pdf_file')
        if not f or not f.name.endswith('.pdf'):
            return JsonResponse({'error': 'Invalid file'}, status=400)
        return JsonResponse({'success': True, 'abstract': extract_abstract_from_pdf(f), 'title': extract_title_from_pdf(f)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def csrf_failure(request, reason=""):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({'success': False, 'error': 'Session expired or security block. Please reload the page and try again.'}, status=403)
    return render(request, "errors/csrf_failure.html", status=403)

@login_required
@require_GET
def api_student_lookup(request, student_id):
    student_id = student_id.strip()
    if not student_id:
        return JsonResponse({'success': False, 'error': 'Student ID required'}, status=400)
    
    # Try searching the Student pre-registration database
    from ..models import Student
    student = Student.objects.filter(student_id=student_id).first()
    
    if student:
        return JsonResponse({
            'success': True,
            'first_name': student.first_name,
            'last_name': student.last_name,
            'email': student.email
        })
    
    # Fallback: search User database
    from django.contrib.auth.models import User
    user = User.objects.filter(username=student_id).first()
    if user:
        return JsonResponse({
            'success': True,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email
        })
        
    return JsonResponse({'success': False, 'error': 'Student ID not found'}, status=404)

@login_required
@require_GET
def api_student_lookup_by_name(request):
    first_name = request.GET.get('first_name', '').strip()
    last_name = request.GET.get('last_name', '').strip()
    if not first_name or not last_name:
        return JsonResponse({'success': False, 'error': 'First name and last name required'}, status=400)
    
    # Try searching the Student pre-registration database
    from ..models import Student
    student = Student.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name).first()
    if student:
        return JsonResponse({
            'success': True,
            'student_id': student.student_id,
            'first_name': student.first_name,
            'last_name': student.last_name,
            'email': student.email
        })
    
    # Fallback: search User database
    from django.contrib.auth.models import User
    user = User.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name).first()
    if user:
        return JsonResponse({
            'success': True,
            'student_id': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email
        })
        
    return JsonResponse({'success': False, 'error': 'Student not found'}, status=404)
