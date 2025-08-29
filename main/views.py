from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.http import FileResponse, Http404, JsonResponse
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django import forms
from .models import Thesis, Category, Submission
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
    elif sort == 'date-desc':
        theses = theses.order_by('-year', 'title')
    elif sort == 'title-asc':
        theses = theses.order_by('title')
    elif sort == 'title-desc':
        theses = theses.order_by('-title')
    elif sort == 'author-asc':
        theses = theses.order_by('author', 'title')
    elif sort == 'author-desc':
        theses = theses.order_by('-author', 'title')

    theses = theses.distinct()

    # Sidebar data with counts
    years = (
        Thesis.objects.values('year')
        .annotate(count=Count('id'))
        .order_by('-year')
    )
    categories = Category.objects.annotate(count=Count('thesis')).order_by('name')
    authors = (
        Thesis.objects.values('author')
        .annotate(count=Count('id'))
        .order_by('author')
    )
    types = (
        Thesis.objects.exclude(thesis_type__isnull=True)
        .exclude(thesis_type__exact='')
        .values('thesis_type')
        .annotate(count=Count('id'))
        .order_by('thesis_type')
    )

    total_results = theses.count()

    context = {
        'theses': theses,
        'categories': categories,
        'years': [
            {'year': y['year'], 'count': y['count']} for y in years
        ],
        'authors': [
            {'name': a['author'], 'count': a['count']} for a in authors
        ],
        'types': [
            {'name': t['thesis_type'], 'count': t['count']} for t in types
        ],
        'total_results': total_results,
        'current_sort': sort,
    }
    return render(request, 'main/categories.html', context)


def category_detail(request, category_name):
    """Browse theses by specific category like Computer Science, Information Systems"""
    try:
        category = Category.objects.get(name__iexact=category_name)
    except Category.DoesNotExist:
        # Handle case-insensitive search for common variations
        category = Category.objects.filter(
            name__icontains=category_name
        ).first()
        
        if not category:
            # Return 404 if no category found
            from django.http import Http404
            raise Http404(f"Category '{category_name}' not found")
    
    theses = Thesis.objects.filter(category=category)
    
    # Get search and filter parameters
    search_query = request.GET.get('search') or ''
    selected_years = request.GET.getlist('year')
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
    
    if selected_authors:
        theses = theses.filter(author__in=selected_authors)
    
    if selected_types:
        theses = theses.filter(thesis_type__in=selected_types)
    
    # Sorting
    if sort == 'date-asc':
        theses = theses.order_by('year', 'title')
    elif sort == 'date-desc':
        theses = theses.order_by('-year', 'title')
    elif sort == 'title-asc':
        theses = theses.order_by('title')
    elif sort == 'title-desc':
        theses = theses.order_by('-title')
    elif sort == 'author-asc':
        theses = theses.order_by('author', 'title')
    elif sort == 'author-desc':
        theses = theses.order_by('-author', 'title')
    
    theses = theses.distinct()
    
    # Get filter data for sidebar
    years = (
        Thesis.objects.filter(category=category)
        .values('year')
        .annotate(count=Count('id'))
        .order_by('-year')
    )
    authors = (
        Thesis.objects.filter(category=category)
        .values('author')
        .annotate(count=Count('id'))
        .order_by('author')
    )
    types = (
        Thesis.objects.filter(category=category)
        .exclude(thesis_type__isnull=True)
        .exclude(thesis_type__exact='')
        .values('thesis_type')
        .annotate(count=Count('id'))
        .order_by('thesis_type')
    )
    
    total_results = theses.count()
    
    context = {
        'category': category,
        'theses': theses,
        'years': [
            {'year': y['year'], 'count': y['count']} for y in years
        ],
        'authors': [
            {'name': a['author'], 'count': a['count']} for a in authors
        ],
        'types': [
            {'name': t['thesis_type'], 'count': t['count']} for t in types
        ],
        'total_results': total_results,
        'current_sort': sort,
    }
    return render(request, 'main/category_detail.html', context)

def student_dashboard(request):
    return render(request, 'main/student_dashboard.html')


@login_required
@require_POST
def create_submission(request):
    title = request.POST.get('thesisTitle') or request.POST.get('title')
    abstract = request.POST.get('abstract', '')
    thesis_type = request.POST.get('degreeLevel', '') or request.POST.get('thesis_type', '')
    specialization = request.POST.get('specialization', '')
    year = request.POST.get('year')
    category_name = request.POST.get('category')
    thesis_file = request.FILES.get('thesisFile')

    if not title:
        return JsonResponse({'ok': False, 'error': 'Title is required'}, status=400)
    if not thesis_file:
        return JsonResponse({'ok': False, 'error': 'Thesis PDF is required'}, status=400)

    category = None
    if category_name:
        category, _ = Category.objects.get_or_create(name=category_name.strip())

    try:
        submission = Submission.objects.create(
            submitter=request.user,
            title=title.strip(),
            author=f"{request.POST.get('firstName', '').strip()} {request.POST.get('lastName', '').strip()}".strip(),
            year=int(year) if year and str(year).isdigit() else None,
            abstract=abstract,
            thesis_type=thesis_type,
            specialization=specialization,
            category=category,
            file=thesis_file,
            status=Submission.STATUS_SUBMITTED,
        )
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

    return JsonResponse({
        'ok': True,
        'id': submission.id,
        'status': submission.status,
        'created_at': submission.created_at,
    })


@login_required
def my_submissions(request):
    submissions = Submission.objects.filter(submitter=request.user)
    return render(request, 'main/my_submissions.html', {'submissions': submissions})


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


# Authentication Views
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
    """Handle both AJAX and regular login requests"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            # Login successful
            user = form.get_user()
            login(request, user)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # AJAX request - return JSON response
                next_url = request.GET.get('next') or request.POST.get('next') or '/'
                return JsonResponse({
                    'success': True,
                    'redirect_url': next_url
                })
            else:
                # Regular request - redirect normally
                return redirect(request.GET.get('next', '/'))
        else:
            # Login failed
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # AJAX request - return JSON with errors
                errors = {}
                
                # Handle form errors
                for field, field_errors in form.errors.items():
                    errors[field] = [str(error) for error in field_errors]
                
                # Handle non-field errors (like invalid credentials)
                if form.non_field_errors():
                    errors['__all__'] = [str(error) for error in form.non_field_errors()]
                
                return JsonResponse({
                    'success': False,
                    'errors': errors
                })
            else:
                # Regular request - redirect back to home with error
                messages.error(request, 'Invalid username or password.')
                return redirect('/')
    
    else:
        # GET request - redirect to home page
        return redirect('/')


@csrf_protect
def signup_view(request):
    """Handle both AJAX and regular signup requests"""
    if request.method == 'POST':
        form = CustomSignupForm(request.POST)
        
        if form.is_valid():
            # Signup successful
            user = form.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # AJAX request - return JSON response
                return JsonResponse({
                    'success': True,
                    'message': 'Account created successfully! Please sign in.',
                    'redirect_url': None  # Don't redirect, just switch to login panel
                })
            else:
                # Regular request - login user and redirect
                login(request, user)
                return redirect('/')
        else:
            # Signup failed
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # AJAX request - return JSON with errors
                errors = {}
                
                # Handle form errors
                for field, field_errors in form.errors.items():
                    errors[field] = [str(error) for error in field_errors]
                
                return JsonResponse({
                    'success': False,
                    'errors': errors
                })
            else:
                # Regular request - redirect back to home with error
                messages.error(request, 'Please correct the errors below.')
                return redirect('/')
    
    else:
        # GET request - redirect to home page
        return redirect('/')