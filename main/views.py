from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q
from django.db.models import Value, IntegerField, Case, When, F, ExpressionWrapper, CharField
from django.db.models.functions import Cast
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.http import FileResponse, Http404, JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django import forms
from .models import Thesis, Category, Submission, DownloadLog
from .utils import search_in_thesis_pdf
from PyPDF2 import PdfReader, PdfWriter
import os, json, io
import re

# ----------------------
# Pages / Landing
# ----------------------
def landing_page(request):
    return render(request, 'main/landing.html')

def about_page(request):
    return render(request, 'main/about.html')

def index_page(request):
    recent_theses = Thesis.objects.order_by('-id')[:6]
    from .models import Department
    departments = Department.objects.all().order_by('name')[:8]
    return render(request, 'main/index.html', {
        'recent_theses': recent_theses,
        'departments': departments,
    })

def categories_page(request):
    theses = Thesis.objects.all()
    search_query = request.GET.get('search') or ''
    search_mode = request.GET.get('search_mode', 'normal')
    selected_years = request.GET.getlist('year')
    selected_descriptors = request.GET.getlist('descriptor')
    selected_authors = request.GET.getlist('author')
    selected_types = request.GET.getlist('type')
    sort = request.GET.get('sort') or 'date-desc'
    selected_department = request.GET.get('department')
    selected_courses = request.GET.getlist('course')

    # Filtering
    if search_query and search_mode != 'deep':
        tokens = [t.lower() for t in re.findall(r"\w+", search_query) if t.strip()]
        score_expr = Value(0, output_field=IntegerField())
        for token in tokens:
            token_score = (
                Case(When(title__icontains=token, then=Value(8)), default=Value(0), output_field=IntegerField()) +
                Case(When(author__icontains=token, then=Value(5)), default=Value(0), output_field=IntegerField()) +
                Case(When(abstract__icontains=token, then=Value(3)), default=Value(0), output_field=IntegerField()) +
                Case(When(keywords__icontains=token, then=Value(3)), default=Value(0), output_field=IntegerField()) +
                Case(When(research_category__icontains=token, then=Value(2)), default=Value(0), output_field=IntegerField()) +
                Case(When(category__name__icontains=token, then=Value(2)), default=Value(0), output_field=IntegerField()) +
                Case(When(department__name__icontains=token, then=Value(2)), default=Value(0), output_field=IntegerField()) +
                Case(When(course__name__icontains=token, then=Value(1)), default=Value(0), output_field=IntegerField())
            )
            # Include year matches if token is numeric
            try:
                year_int = int(token)
                token_score = token_score + Case(When(year=year_int, then=Value(2)), default=Value(0), output_field=IntegerField())
            except Exception:
                pass
            score_expr = score_expr + token_score
        theses = theses.annotate(score=ExpressionWrapper(score_expr, output_field=IntegerField())).filter(score__gt=0)

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

    # Department filter (by ID)
    if selected_department and selected_department != 'all':
        try:
            dept_id = int(selected_department)
            theses = theses.filter(department__id=dept_id)
        except ValueError:
            pass

    # Course filter (by ID)
    if selected_courses:
        try:
            course_ids = [int(cid) for cid in selected_courses if cid.isdigit()]
            if course_ids:
                theses = theses.filter(course__id__in=course_ids)
        except ValueError:
            pass

    # Sorting
    sort_options = {
        'date-asc': ('year', 'title'),
        'date-desc': ('-year', 'title'),
        'title-asc': ('title',),
        'title-desc': ('-title',),
        'author-asc': ('author', 'title'),
        'author-desc': ('-author', 'title')
    }
    # Order by relevance score first if searching, then chosen sort
    base_order = sort_options.get(sort, ('-year', 'title'))
    if search_query and search_mode != 'deep':
        theses = theses.order_by('-score', *base_order)
    else:
        theses = theses.order_by(*base_order)
    theses = theses.distinct()

    # If deep search is enabled, scan PDFs and keep only matches
    matched_theses = None
    if search_query and search_mode == 'deep':
        matched_theses_list = []
        for thesis in theses:
            # Skip if there is no file
            if not thesis.file:
                continue
            deep_search_results = search_in_thesis_pdf(thesis, search_query)
            if deep_search_results.get('found'):
                thesis.deep_search_results = deep_search_results
                matched_theses_list.append(thesis)
        theses = matched_theses_list

    # --- Prepare keywords and research categories lists ---
    for thesis in theses:
        thesis.keywords_list = [k.strip() for k in (thesis.keywords or "").split(',') if k.strip()]
        thesis.research_categories_list = [c.strip() for c in (thesis.research_category or "").split(',') if c.strip()]
        # Ensure attribute exists in normal mode
        if not getattr(thesis, 'deep_search_results', None):
            thesis.deep_search_results = None

    # Sidebar
    from .models import Department, Course
    departments = Department.objects.all().order_by('name')
    # Only show courses for the selected department
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

    # Compute total after deep filtering (list vs QuerySet)
    total_results = len(theses) if isinstance(theses, list) else theses.count()
    context = {
        'theses': theses,
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
    }
    return render(request, 'main/categories.html', context)


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
        tokens = [t.lower() for t in re.findall(r"\w+", search_query) if t.strip()]
        theses = theses.annotate(coauthor_json_text=Cast('co_authors', output_field=CharField()))
        score_expr = Value(0, output_field=IntegerField())
        for token in tokens:
            token_score = (
                Case(When(title__icontains=token, then=Value(8)), default=Value(0), output_field=IntegerField()) +
                Case(When(author__icontains=token, then=Value(5)), default=Value(0), output_field=IntegerField()) +
                Case(When(coauthor_json_text__icontains=token, then=Value(5)), default=Value(0), output_field=IntegerField()) +
                Case(When(abstract__icontains=token, then=Value(3)), default=Value(0), output_field=IntegerField()) +
                Case(When(keywords__icontains=token, then=Value(3)), default=Value(0), output_field=IntegerField()) +
                Case(When(research_category__icontains=token, then=Value(2)), default=Value(0), output_field=IntegerField()) +
                Case(When(category__name__icontains=token, then=Value(2)), default=Value(0), output_field=IntegerField()) +
                Case(When(department__name__icontains=token, then=Value(2)), default=Value(0), output_field=IntegerField()) +
                Case(When(course__name__icontains=token, then=Value(1)), default=Value(0), output_field=IntegerField())
            )
            try:
                year_int = int(token)
                token_score = token_score + Case(When(year=year_int, then=Value(2)), default=Value(0), output_field=IntegerField())
            except Exception:
                pass
            score_expr = score_expr + token_score
        theses = theses.annotate(score=ExpressionWrapper(score_expr, output_field=IntegerField())).filter(score__gt=0)

    if selected_years:
        numeric_years = [int(y) for y in selected_years if str(y).isdigit()]
        if numeric_years:
            theses = theses.filter(year__in=numeric_years)

    if selected_authors:
        theses = theses.filter(author__in=selected_authors)

    if selected_types:
        theses = theses.filter(thesis_type__in=selected_types)

    # Sorting
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
        theses = theses.order_by('-score', *base_order)
    else:
        theses = theses.order_by(*base_order)
    theses = theses.distinct()

    # Sidebar
    years = Thesis.objects.filter(category=category).values('year').annotate(count=Count('id')).order_by('-year')
    authors = Thesis.objects.filter(category=category).values('author').annotate(count=Count('id')).order_by('author')
    types = Thesis.objects.filter(category=category).exclude(thesis_type__isnull=True)\
                          .exclude(thesis_type__exact='').values('thesis_type')\
                          .annotate(count=Count('id')).order_by('thesis_type')

    total_results = theses.count()
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

# ----------------------
# Student / Dashboard
# ----------------------
@login_required
def student_dashboard(request):
    categories = Category.objects.all().order_by('name')
    return render(request, 'main/student_dashboard.html', {
        'categories': categories
    })

@login_required
@user_passes_test(lambda u: u.is_staff)  # Only allow admin/staff users
def admin_dashboard(request):
    """Admin dashboard overview"""
    context = {
        'total_theses': Thesis.objects.count(),
        'total_users': User.objects.count(),
        'pending_submissions': Submission.objects.filter(status='Pending').count(),
        'approved_theses': Submission.objects.filter(status='Approved').count(),
        'download_logs': DownloadLog.objects.count(),
    }
    return render(request, 'main/admin_dashboard.html', context)


@login_required
@require_POST
def create_submission(request):
    title = request.POST.get('thesisTitle') or request.POST.get('title')
    abstract = request.POST.get('abstract', '')
    keywords = request.POST.get('keywords', '')
    research_category = request.POST.get('research_category', '')
    expected_completion = request.POST.get('expectedCompletion') or None
    specialization = request.POST.get('specialization', '')
    year = request.POST.get('year')
    academic_level_id = request.POST.get('academic_level')
    department_id = request.POST.get('department')
    course_id = request.POST.get('course')
    thesis_file = request.FILES.get('thesisFile')
    approval_sheet = request.FILES.get('approval_sheet')

    # Validation
    errors = []
    if not title:
        errors.append('Title is required')
    if not thesis_file:
        errors.append('Thesis PDF is required')
    if not approval_sheet:
        errors.append('Approval sheet is required')
    if not academic_level_id:
        errors.append('Academic Level is required')
    if not department_id:
        errors.append('Department is required')
    if not course_id:
        errors.append('Course/Program is required')

    if errors:
        messages.error(request, 'Please correct the following errors: ' + ', '.join(errors))
        return redirect('student_dashboard')

    # Get the actual objects from IDs
    academic_level = None
    department = None
    course = None
    
    try:
        if academic_level_id:
            academic_level = Category.objects.get(id=academic_level_id)
        if department_id:
            from .models import Department
            department = Department.objects.get(id=department_id)
        if course_id:
            from .models import Course
            course = Course.objects.get(id=course_id)
    except (Category.DoesNotExist, Department.DoesNotExist, Course.DoesNotExist):
        messages.error(request, 'Invalid academic structure selection')
        return redirect('student_dashboard')

    try:
        # Parse structured co-authors from form naming convention coauthors[i][..]
        co_authors_data = []
        i = 0
        while True:
            first = request.POST.get(f'coauthors[{i}][first_name]', '').strip()
            last = request.POST.get(f'coauthors[{i}][last_name]', '').strip()
            sid = request.POST.get(f'coauthors[{i}][student_id]', '').strip()
            email = request.POST.get(f'coauthors[{i}][email]', '').strip()
            if not any([first, last, sid, email]):
                break  # stop if no further entries
            co_authors_data.append({
                'first_name': first,
                'last_name': last,
                'student_id': sid,
                'email': email,
            })
            i += 1

        # Supervisor details
        supervisor_name = request.POST.get('supervisorName', '').strip()
        supervisor_email = request.POST.get('supervisorEmail', '').strip()
        supervisor_department = request.POST.get('supervisorDepartment', '').strip()
        supervisor_title = request.POST.get('supervisorTitle', '').strip()
        co_supervisor_name = request.POST.get('coSupervisorName', '').strip()
        co_supervisor_email = request.POST.get('coSupervisorEmail', '').strip()

        submission = Submission.objects.create(
            submitter=request.user,
            title=title.strip(),
            author=f"{request.POST.get('firstName', '').strip()} {request.POST.get('lastName', '').strip()}".strip(),
            year=int(year) if year and str(year).isdigit() else None,
            abstract=abstract,
            keywords=keywords,
            research_category=research_category,
            expected_completion=expected_completion or None,
            specialization=specialization,
            category=academic_level,
            department=department,
            course=course,
            file=thesis_file,
            approval_sheet=approval_sheet,
            supervisor_name=supervisor_name,
            supervisor_email=supervisor_email,
            supervisor_department=supervisor_department,
            supervisor_title=supervisor_title,
            co_supervisor_name=co_supervisor_name,
            co_supervisor_email=co_supervisor_email,
            status=Submission.STATUS_PENDING,
        )
        
        # Create co-authors using the relational approach
        for coauthor_data in co_authors_data:
            from .models import SubmissionCoAuthor
            SubmissionCoAuthor.objects.create(
                submission=submission,
                first_name=coauthor_data['first_name'],
                last_name=coauthor_data['last_name'],
                student_id=coauthor_data['student_id'],
                email=coauthor_data['email'],
            )
        
        messages.success(request, f'Thesis "{submission.title}" submitted successfully!')
        return redirect('my_submissions')
        
    except Exception as e:
        messages.error(request, f'Error submitting thesis: {str(e)}')
        return redirect('student_dashboard')


@login_required
def my_submissions(request):
    submissions = Submission.objects.filter(submitter=request.user)
    return render(request, 'main/my_submissions.html', {'submissions': submissions})


def thesis_detail(request, pk: int):
    thesis = get_object_or_404(Thesis, pk=pk)
    is_authenticated = request.user.is_authenticated
    return render(request, 'main/thesis_detail.html', {
        'thesis': thesis,
        'is_authenticated': is_authenticated
    })


def view_thesis_file(request, pk):
    thesis = get_object_or_404(Thesis, pk=pk)
    if not thesis.file:
        raise Http404('File not found.')
    
    # For non-authenticated users, we'll serve a restricted version
    # This will be handled by a separate view that creates a limited PDF
    if not request.user.is_authenticated:
        return restricted_view_thesis_file(request, pk)
    
    response = FileResponse(thesis.file.open('rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(thesis.file.name)}"'
    return response


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

def download_thesis_file(request, pk):
    """
    Handles thesis file downloads with authentication checks
    Logs the download event for auditing.
    """
    # Check if user is authenticated
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False, 
                'error': 'Please log in to download thesis files.', 
                'require_login': True
            }, status=401)
        else:
            messages.error(request, 'Please log in to download thesis files.')
            return redirect('/')

    # User is authenticated - proceed with file download
    thesis = get_object_or_404(Thesis, pk=pk)
    if not thesis.file:
        raise Http404('File not found.')

    try:
        # Log the download - make sure this happens
        DownloadLog.objects.create(
            user=request.user,
            thesis=thesis,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]  # Truncate long user agents
        )
        
        # Create file response with proper headers for download
        response = FileResponse(thesis.file.open('rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(thesis.file.name)}"'
        return response
        
    except Exception as e:
        # If logging fails, still allow download but log the error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Download logging failed for thesis {pk}: {str(e)}")
        
        # Still provide the file download
        response = FileResponse(thesis.file.open('rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(thesis.file.name)}"'
        return response


def restricted_view_thesis_file(request, pk):
    """
    Serves a preview version of thesis files for non-authenticated users
    
    This function creates a restricted PDF containing only the first 3 pages
    of the original thesis, allowing users to preview content before logging in.
    
    Args:
        request: Django request object
        pk: Primary key of the thesis to preview
        
    Returns:
        HttpResponse: PDF response with limited pages
        Http404: If thesis or file not found
    """
    thesis = get_object_or_404(Thesis, pk=pk)
    if not thesis.file:
        raise Http404('File not found.')
    
    try:
        # Initialize PDF processing components
        pdf_reader = PdfReader(thesis.file.open('rb'))
        pdf_writer = PdfWriter()
        
        # Determine how many pages to include (max 3 for preview)
        max_pages = min(3, len(pdf_reader.pages))
        for page_num in range(max_pages):
            pdf_writer.add_page(pdf_reader.pages[page_num])
        
        # Create a watermark page for the restriction notice
        if max_pages < 3:
            # If PDF has less than 3 pages, add a restriction notice page
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            p.drawString(100, 750, "Thesis Library - Preview Mode")
            p.drawString(100, 700, f"Title: {thesis.title}")
            p.drawString(100, 650, f"Author: {thesis.author}")
            p.drawString(100, 600, "This is a preview of the first few pages.")
            p.drawString(100, 550, "Please log in to view the complete thesis and download the full document.")
            p.showPage()
            p.save()
            
            # Add the watermark page to the PDF
            watermark_reader = PdfReader(buffer)
            pdf_writer.add_page(watermark_reader.pages[0])
        
        # Create the response
        output_buffer = io.BytesIO()
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)
        
        response = HttpResponse(output_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="preview_{os.path.basename(thesis.file.name)}"'
        return response
        
    except Exception as e:
        # If PDF processing fails, return a simple error message
        return HttpResponse(f"Error processing PDF: {str(e)}", status=500)


# ----------------------
# Authentication
# ----------------------
class CustomSignupForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


@csrf_protect
def login_view(request):
    """Handle regular, AJAX, and JSON login"""
    if request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                username = data.get('username')
                password = data.get('password')
                user = authenticate(request, username=username, password=password)
                if user:
                    login(request, user)
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False, 'error': 'Invalid credentials'}, status=400)
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
        else:
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                user = form.get_user()
                login(request, user)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    next_url = request.POST.get('next') or request.GET.get('next') or '/'
                    return JsonResponse({'success': True, 'redirect_url': next_url})
                else:
                    next_url = request.POST.get('next') or request.GET.get('next') or '/'
                    return redirect(next_url)
            else:
                errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'errors': errors})
                else:
                    messages.error(request, 'Invalid username or password.')
                    return redirect('/')
    return redirect('/')


@csrf_exempt
def signup_view(request):
    """Handle form POST, AJAX POST, and raw JSON POST"""
    if request.method == 'POST':
        # JSON POST
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                username = data.get("username")
                email = data.get("email")
                password = data.get("password")
                
                if not username or not password or not email:
                    return JsonResponse({"success": False, "error": "Username, email, and password are required"}, status=400)

                if User.objects.filter(username=username).exists():
                    return JsonResponse({"success": False, "error": "Username already taken"}, status=400)

                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                return JsonResponse({"success": True, "message": "Account created successfully!"})

            except Exception as e:
                return JsonResponse({"success": False, "error": str(e)}, status=500)

        # Form / AJAX POST
        else:
            form = CustomSignupForm(request.POST)
            if form.is_valid():
                user = form.save()
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Account created successfully! Please sign in.', 'redirect_url': None})
                else:
                    login(request, user)
                    return redirect('/')
            else:
                errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'errors': errors})
                else:
                    messages.error(request, 'Please correct the errors below.')
                    return redirect('/')
    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


# ----------------------
# API Endpoints for Academic Structure
# ----------------------
@require_GET
def api_departments(request, category_id):
    """Get departments for a specific category"""
    try:
        category = Category.objects.get(id=category_id)
        departments = category.departments.all().order_by('name')
        data = {
            'departments': [
                {
                    'id': dept.id,
                    'name': dept.name
                } for dept in departments
            ]
        }
        return JsonResponse(data)
    except Category.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def api_courses(request, department_id):
    """Get courses for a specific department"""
    try:
        from .models import Department
        department = Department.objects.get(id=department_id)
        courses = department.courses.all().order_by('name')
        data = {
            'courses': [
                {
                    'id': course.id,
                    'name': course.name
                } for course in courses
            ]
        }
        return JsonResponse(data)
    except Department.DoesNotExist:
        return JsonResponse({'error': 'Department not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def csrf_failure(request, reason=""):
    return render(request, "errors/csrf_failure.html", status=403)
