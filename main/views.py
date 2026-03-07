import shutil
from datetime import timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q, OuterRef, Subquery
from django.db.models import Value, IntegerField, Case, When, F, ExpressionWrapper, CharField, DateTimeField
from django.db.models.functions import Concat
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.db.models.functions import Cast, TruncMonth
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.http import FileResponse, Http404, JsonResponse, HttpResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from datetime import datetime
from django.contrib import messages
from django import forms
from .models import Thesis, Category, Submission, DownloadLog, RejectedThesis, Course, Department, Student, Professor, VerificationCode, PasswordResetCode
from authapp.models import Profile
from django.core.mail import send_mail
from django.core.paginator import Paginator
from collections import Counter
from django.conf import settings
import random
import string
from .utils import search_in_thesis_pdf, suggest_query_correction, deep_filter_theses_by_pdf, get_thesis_preview, extract_abstract_from_pdf, extract_title_from_pdf
from django.utils import timezone
from PyPDF2 import PdfReader, PdfWriter
import fitz
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


@login_required
def profile_card(request):
    """Display a simple profile card for the logged-in user."""
    user = request.user
    student_record = Student.objects.filter(student_id=user.username).first()
    professor_record = Professor.objects.filter(professor_id=user.username).first()

    def build_name():
        if student_record:
            return f"{student_record.first_name or ''} {student_record.last_name or ''}".strip()
        if professor_record:
            return f"{professor_record.first_name or ''} {professor_record.last_name or ''}".strip()
        if user.first_name or user.last_name:
            return f"{user.first_name or ''} {user.last_name or ''}".strip()
        return user.username

    full_name = build_name()
    contact_email = (
        (student_record.email if student_record and student_record.email else None)
        or (professor_record.email if professor_record and professor_record.email else None)
        or user.email
    )
    identifier = (
        student_record.student_id if student_record else
        professor_record.professor_id if professor_record else
        user.username
    )
    profile_obj, _ = Profile.objects.get_or_create(user=user)
    role = profile_obj.get_role_display()

    submissions_qs = Submission.objects.filter(submitter=user)
    recent_submission = submissions_qs.order_by('-created_at').first()

    initials = ''.join([part[0] for part in full_name.split() if part])[:2].upper()
    if not initials:
        initials = (user.username[:2] or "??").upper()

    profile = {
        "full_name": full_name,
        "role": role,
        "role_code": profile_obj.role,
        "username": user.username,
        "identifier": identifier,
        "email": contact_email or "Not provided",
        "joined": user.date_joined,
        "last_login": user.last_login,
        "submission_count": submissions_qs.count(),
        "recent_submission_title": recent_submission.title if recent_submission else None,
        "recent_submission_date": recent_submission.created_at if recent_submission else None,
        "initials": initials,
        "is_admin": profile_obj.role in [Profile.ADMIN, Profile.LIBRARIAN],
        "has_dashboard": profile_obj.role not in [Profile.ADMIN, Profile.LIBRARIAN],
    }

    return render(request, 'main/profile_card.html', {"profile": profile})

def categories_page(request):
    theses = Thesis.objects.all()
    search_query = request.GET.get('search') or ''
    
    # Permission check for Deep Search
    can_full_view = request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role in [Profile.ADMIN, Profile.LIBRARIAN]
    
    search_mode = request.GET.get('search_mode', 'normal')
    if search_mode == 'deep' and not can_full_view:
        search_mode = 'normal'
        messages.warning(request, "Deep search (searching inside PDF contents) is restricted to Administrators and Librarians.")
    selected_years = request.GET.getlist('year')
    selected_descriptors = request.GET.getlist('descriptor')
    selected_authors = request.GET.getlist('author')
    selected_types = request.GET.getlist('type')
    sort = request.GET.get('sort') or 'date-desc'
    selected_department = request.GET.get('department')
    selected_courses = request.GET.getlist('course')

    # Optional fuzzy suggestion (only for normal mode)
    did_you_mean = None
    effective_query = search_query
    if search_query:
        try:
            # Build a corpus of searchable tokens
            title_list = list(Thesis.objects.values_list('title', flat=True))
            author_list = list(Thesis.objects.values_list('author', flat=True))
            keyword_list = [kw.strip() for kw in Thesis.objects.exclude(keywords__isnull=True).exclude(keywords__exact='').values_list('keywords', flat=True)]
            # Split comma-separated keywords
            split_keywords = []
            for kw in keyword_list:
                split_keywords.extend([t.strip() for t in kw.split(',') if t.strip()])
            research_list = [rc.strip() for rc in Thesis.objects.exclude(research_category__isnull=True).exclude(research_category__exact='').values_list('research_category', flat=True)]
            # Split comma-separated research categories
            split_research = []
            for rc in research_list:
                split_research.extend([t.strip() for t in rc.split(',') if t.strip()])
            # Departments and courses
            from .models import Department, Course
            dept_names = list(Department.objects.values_list('name', flat=True))
            course_names = list(Course.objects.values_list('name', flat=True))

            corpus = [s for s in (title_list + author_list + split_keywords + split_research + dept_names + course_names) if s]

            suggestion, confidence = suggest_query_correction(search_query, corpus)
            if suggestion and suggestion.strip().lower() != search_query.strip().lower():
                did_you_mean = suggestion
                if search_mode == 'deep':
                    effective_query = suggestion
        except Exception:
            did_you_mean = None

    # Filtering by search
    if search_query:
        if search_mode == 'deep':
            # Deep search: only by PDF contents
            # Apply non-search filters first to limit the set before PDF scanning
            pass  # handled below; we will scan after applying facet filters
        else:
            # Normal search: search metadata fields (the card)
            STOPWORDS = {
                'a', 'an', 'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'as', 
                'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 
                'did', 'but', 'if', 'then', 'else', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 
                'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 
                'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 
                'should', 'now', 'thesis', 'study', 'research', 'library'
            }
            
            # Annotate co-authors and other fields for searching
            theses = theses.annotate(
                coauthor_json_text=Concat(
                    F('co_authors__first_name'), Value(' '), F('co_authors__last_name'), 
                    output_field=CharField()
                )
            )
            
            # Exact Phrase Matching (High Weight)
            phrase_score = (
                Case(When(title__icontains=search_query, then=Value(150)), default=Value(0), output_field=IntegerField()) +
                Case(When(abstract__icontains=search_query, then=Value(100)), default=Value(0), output_field=IntegerField()) +
                Case(When(author__icontains=search_query, then=Value(80)), default=Value(0), output_field=IntegerField()) +
                Case(When(keywords__icontains=search_query, then=Value(80)), default=Value(0), output_field=IntegerField()) +
                Case(When(coauthor_json_text__icontains=search_query, then=Value(70)), default=Value(0), output_field=IntegerField()) +
                Case(When(department__name__icontains=search_query, then=Value(50)), default=Value(0), output_field=IntegerField()) +
                Case(When(course__name__icontains=search_query, then=Value(40)), default=Value(0), output_field=IntegerField())
            )
            
            # Token-based Matching
            tokens = [t.lower() for t in re.findall(r"\w+", search_query) if t.strip()]
            search_tokens = [t for t in tokens if t not in STOPWORDS or len(t) > 3]
            if not search_tokens and tokens: search_tokens = tokens
            
            token_score_expr = Value(0)
            try:
                from main.nlp_utils import get_lemmas
            except Exception:
                def get_lemmas(w): return {w}
                
            for token in search_tokens:
                lemmas = get_lemmas(token)
                title_q = Q(); author_q = Q(); abstract_q = Q(); keywords_q = Q()
                research_cat_q = Q(); cat_name_q = Q(); dept_name_q = Q(); course_name_q = Q()
                coauthor_q = Q()
                
                for lemma in lemmas:
                    title_q |= Q(title__icontains=lemma); author_q |= Q(author__icontains=lemma)
                    abstract_q |= Q(abstract__icontains=lemma); keywords_q |= Q(keywords__icontains=lemma)
                    research_cat_q |= Q(research_category__icontains=lemma)
                    cat_name_q |= Q(category__name__icontains=lemma)
                    dept_name_q |= Q(department__name__icontains=lemma)
                    course_name_q |= Q(course__name__icontains=lemma)
                    coauthor_q |= Q(coauthor_json_text__icontains=lemma)
                
                token_score = (
                    Case(When(title_q, then=Value(30)), default=Value(0), output_field=IntegerField()) +
                    Case(When(author_q, then=Value(15)), default=Value(0), output_field=IntegerField()) +
                    Case(When(coauthor_q, then=Value(15)), default=Value(0), output_field=IntegerField()) +
                    Case(When(abstract_q, then=Value(10)), default=Value(0), output_field=IntegerField()) +
                    Case(When(keywords_q, then=Value(10)), default=Value(0), output_field=IntegerField()) +
                    Case(When(research_cat_q, then=Value(5)), default=Value(0), output_field=IntegerField()) +
                    Case(When(cat_name_q, then=Value(5)), default=Value(0), output_field=IntegerField()) +
                    Case(When(dept_name_q, then=Value(5)), default=Value(0), output_field=IntegerField()) +
                    Case(When(course_name_q, then=Value(5)), default=Value(0), output_field=IntegerField())
                )
                try:
                    year_int = int(token)
                    if 1900 < year_int < 2100:
                        token_score += Case(When(year=year_int, then=Value(20)), default=Value(0), output_field=IntegerField())
                except: pass
                token_score_expr += token_score
                
            theses = theses.annotate(score=ExpressionWrapper(phrase_score + token_score_expr, output_field=IntegerField())).filter(score__gt=0)
            
            # Default sorting by score if searching
            if not sort or sort == 'date-desc':
                theses = theses.order_by('-score', '-year')
            else:
                sort_map = {
                    'date-asc': ('year', '-score'), 'date-desc': ('-year', '-score'),
                    'title-asc': ('title', '-score'), 'title-desc': ('-title', '-score'),
                    'author-asc': ('author', '-score'), 'author-desc': ('-author', '-score')
                }
                theses = theses.order_by(*sort_map.get(sort, ('-score', '-year')))

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

    # If deep search is enabled, refine suggestion using PDF previews after facet filters
    if search_query and search_mode == 'deep':
        try:
            # Limit to a reasonable number of items to avoid heavy IO
            sample_theses = list(theses[:50])
            pdf_tokens = []
            for t in sample_theses:
                if not getattr(t, 'file', None):
                    continue
                preview_text = get_thesis_preview(t, max_pages=2) or ''
                # collect words as candidate tokens
                pdf_tokens.extend([w for w in re.findall(r"\w+", preview_text) if w])
            suggestion_pdf, conf_pdf = suggest_query_correction(search_query, pdf_tokens)
            if suggestion_pdf and suggestion_pdf.strip().lower() != search_query.strip().lower():
                did_you_mean = suggestion_pdf
                effective_query = suggestion_pdf
        except Exception:
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
    base_order = sort_options.get(sort, ('-year', 'title'))

    # Apply deep search after facet filters, before final ordering
    if search_query and search_mode == 'deep':
        # Convert to list before scanning PDFs
        theses_list = list(theses)
        theses = deep_filter_theses_by_pdf(theses_list, effective_query)
        # In deep mode we keep list semantics; no .order_by on list
    else:
        # Order by relevance score first if searching, then chosen sort
        if search_query:
            theses = theses.order_by('-score', *base_order)
        else:
            theses = theses.order_by(*base_order)
        
        # Deduplicate manually, keeping the first occurrence (highest score due to order_by)
        unique_theses = []
        seen = set()
        for t in theses:
            if t.id not in seen:
                seen.add(t.id)
                unique_theses.append(t)
        theses = unique_theses

    # If deep search is enabled, scan PDFs and keep only matches
    matched_theses = None
    if search_query and search_mode == 'deep':
        matched_theses_list = []
        for thesis in theses:
            # Skip if there is no file
            if not thesis.file:
                continue
            deep_search_results = search_in_thesis_pdf(thesis, effective_query)
            if deep_search_results.get('found'):
                thesis.deep_search_results = deep_search_results
                thesis.deep_search_query = effective_query
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
        'did_you_mean': did_you_mean,
        'effective_query': effective_query,
        'can_full_view': can_full_view,
    }
    return render(request, 'main/categories.html', context)

@csrf_exempt
def archive_old_theses(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    User = get_user_model()
    system_user = User.objects.filter(is_superuser=True).first()  # pick any admin as the "system" user
    if not system_user:
        return JsonResponse({"error": "No admin user found to log actions."}, status=500)

    current_year = datetime.now().year
    cutoff_year = current_year - 10

    old_theses = Thesis.objects.filter(year__lte=cutoff_year)
    archived_count = 0

    for thesis in old_theses:

        # Delete related co-authors
        thesis.co_authors.all().delete()

        # Delete related approved Submissions
        Submission.objects.filter(
            title=thesis.title,
            author=thesis.author,
            year=thesis.year,
            status=Submission.STATUS_APPROVED
        ).delete()

        # Move thesis file if it exists
        if thesis.file and thesis.file.name:
            old_path = thesis.file.path
            archive_dir = os.path.join(settings.MEDIA_ROOT, "thesis_files", "Archived")
            os.makedirs(archive_dir, exist_ok=True)

            filename = os.path.basename(old_path)
            new_path = os.path.join(archive_dir, filename)

            if os.path.exists(old_path):
                shutil.move(old_path, new_path)
                thesis.file.name = f"thesis_files/Archived/{filename}"
                thesis.save()
                archived_count += 1

        # Log before deletion
        LogEntry.objects.log_action(
            user_id=system_user.id,
            content_type_id=ContentType.objects.get_for_model(Thesis).pk,
            object_id=thesis.pk,
            object_repr=str(thesis),
            action_flag=DELETION,
            change_message="Archived thesis older than 10 years"
        )

        # Delete the Thesis record
        thesis.delete()

    return JsonResponse({"archived": archived_count})


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
        STOPWORDS = {
            'a', 'an', 'the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'as', 
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 
            'did', 'but', 'if', 'then', 'else', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 
            'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 
            'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 
            'should', 'now', 'thesis', 'study', 'research', 'library'
        }
        
        theses = theses.annotate(
            coauthor_json_text=Concat(
                F('co_authors__first_name'), Value(' '), F('co_authors__last_name'), 
                output_field=CharField()
            )
        )
        
        phrase_score = (
            Case(When(title__icontains=search_query, then=Value(150)), default=Value(0), output_field=IntegerField()) +
            Case(When(abstract__icontains=search_query, then=Value(100)), default=Value(0), output_field=IntegerField()) +
            Case(When(author__icontains=search_query, then=Value(80)), default=Value(0), output_field=IntegerField()) +
            Case(When(keywords__icontains=search_query, then=Value(80)), default=Value(0), output_field=IntegerField()) +
            Case(When(coauthor_json_text__icontains=search_query, then=Value(70)), default=Value(0), output_field=IntegerField()) +
            Case(When(department__name__icontains=search_query, then=Value(50)), default=Value(0), output_field=IntegerField()) +
            Case(When(course__name__icontains=search_query, then=Value(40)), default=Value(0), output_field=IntegerField())
        )
        
        tokens = [t.lower() for t in re.findall(r"\w+", search_query) if t.strip()]
        search_tokens = [t for t in tokens if t not in STOPWORDS or len(t) > 3]
        if not search_tokens and tokens: search_tokens = tokens
        
        token_score_expr = Value(0)
        try:
            from main.nlp_utils import get_lemmas
        except Exception:
            def get_lemmas(w): return {w}
            
        for token in search_tokens:
            lemmas = get_lemmas(token)
            title_q = Q(); author_q = Q(); abstract_q = Q(); keywords_q = Q()
            research_cat_q = Q(); cat_name_q = Q(); dept_name_q = Q(); course_name_q = Q()
            coauthor_q = Q()
            
            for lemma in lemmas:
                title_q |= Q(title__icontains=lemma); author_q |= Q(author__icontains=lemma)
                abstract_q |= Q(abstract__icontains=lemma); keywords_q |= Q(keywords__icontains=lemma)
                research_cat_q |= Q(research_category__icontains=lemma)
                cat_name_q |= Q(category__name__icontains=lemma)
                dept_name_q |= Q(department__name__icontains=lemma)
                course_name_q |= Q(course__name__icontains=lemma)
                coauthor_q |= Q(coauthor_json_text__icontains=lemma)
            
            token_score = (
                Case(When(title_q, then=Value(30)), default=Value(0), output_field=IntegerField()) +
                Case(When(author_q, then=Value(15)), default=Value(0), output_field=IntegerField()) +
                Case(When(coauthor_q, then=Value(15)), default=Value(0), output_field=IntegerField()) +
                Case(When(abstract_q, then=Value(10)), default=Value(0), output_field=IntegerField()) +
                Case(When(keywords_q, then=Value(10)), default=Value(0), output_field=IntegerField()) +
                Case(When(research_cat_q, then=Value(5)), default=Value(0), output_field=IntegerField()) +
                Case(When(cat_name_q, then=Value(5)), default=Value(0), output_field=IntegerField()) +
                Case(When(dept_name_q, then=Value(5)), default=Value(0), output_field=IntegerField()) +
                Case(When(course_name_q, then=Value(5)), default=Value(0), output_field=IntegerField())
            )
            try:
                year_int = int(token)
                if 1900 < year_int < 2100:
                    token_score += Case(When(year=year_int, then=Value(20)), default=Value(0), output_field=IntegerField())
            except: pass
            token_score_expr += token_score
            
        theses = theses.annotate(score=ExpressionWrapper(phrase_score + token_score_expr, output_field=IntegerField())).filter(score__gt=0)

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
        if not sort or sort == 'date-desc':
            theses = theses.order_by('-score', '-year')
        else:
            sort_map = {
                'date-asc': ('year', '-score'), 'date-desc': ('-year', '-score'),
                'title-asc': ('title', '-score'), 'title-desc': ('-title', '-score'),
                'author-asc': ('author', '-score'), 'author-desc': ('-author', '-score')
            }
            theses = theses.order_by(*sort_map.get(sort, ('-score', '-year')))
    else:
        theses = theses.order_by(*base_order)
        
    unique_theses = []
    seen = set()
    for t in theses:
        if t.id not in seen:
            seen.add(t.id)
            unique_theses.append(t)
    theses = unique_theses

    # Sidebar
    years = Thesis.objects.filter(category=category).values('year').annotate(count=Count('id')).order_by('-year')
    authors = Thesis.objects.filter(category=category).values('author').annotate(count=Count('id')).order_by('author')
    types = Thesis.objects.filter(category=category).exclude(thesis_type__isnull=True)\
                          .exclude(thesis_type__exact='').values('thesis_type')\
                          .annotate(count=Count('id')).order_by('thesis_type')

    total_results = len(theses)
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
    
    # Get user data from Student or Professor database for autofill
    user_data = {
        'first_name': '',
        'last_name': '',
        'email': '',
        'student_id': ''
    }
    
    # The username is the student_id or professor_id
    user_id = request.user.username
    
    # Try to get student data
    try:
        student = Student.objects.get(student_id=user_id)
        user_data['first_name'] = student.first_name or ''
        user_data['last_name'] = student.last_name or ''
        user_data['email'] = student.email or request.user.email or ''
        user_data['student_id'] = student.student_id
    except Student.DoesNotExist:
        # Try to get professor data
        try:
            professor = Professor.objects.get(professor_id=user_id)
            user_data['first_name'] = professor.first_name or ''
            user_data['last_name'] = professor.last_name or ''
            user_data['email'] = professor.email or request.user.email or ''
            user_data['student_id'] = professor.professor_id  # Use professor_id as student_id for form
        except Professor.DoesNotExist:
            # Fallback to user model data if Student/Professor record doesn't exist
            user_data['first_name'] = request.user.first_name or ''
            user_data['last_name'] = request.user.last_name or ''
            user_data['email'] = request.user.email or ''
            user_data['student_id'] = user_id
    
    return render(request, 'main/student_dashboard.html', {
        'categories': categories,
        'user_data': user_data
    })

def log_admin_action(user, obj, action_flag, message):
    """Helper to log custom admin actions."""
    from django.contrib.admin.models import LogEntry
    from django.contrib.contenttypes.models import ContentType

    LogEntry.objects.log_action(
        user_id=user.id,
        content_type_id=ContentType.objects.get_for_model(obj).pk,
        object_id=obj.pk,
        object_repr=str(obj),
        action_flag=action_flag,
        change_message=message,
    )

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role in [Profile.ADMIN, Profile.LIBRARIAN])  # Only allow admin/librarian
def admin_dashboard(request):
    total_theses = Thesis.objects.count()
    total_users = User.objects.count()
    pending_submissions = Submission.objects.filter(status='pending').count()
    approved_theses = Submission.objects.filter(status='approved').count()
    download_logs = DownloadLog.objects.count()

    monthly_trends = (
        Submission.objects
        .annotate(month=TruncMonth('created_at'))
        .values('month', 'status')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    # Group data into a structure suitable for Chart.js
    months = []
    approved_data, pending_data, rejected_data = [], [], []

    from django.utils.dateformat import DateFormat
    from django.utils.formats import get_format

    # Get unique months in order
    for entry in sorted({item['month'] for item in monthly_trends if item['month']}):
        months.append(DateFormat(entry).format('M'))  # e.g., Jan, Feb, Mar
        month_entries = [e for e in monthly_trends if e['month'] == entry]

        approved_data.append(next((e['count'] for e in month_entries if e['status'] == 'approved'), 0))
        pending_data.append(next((e['count'] for e in month_entries if e['status'] == 'pending'), 0))
        rejected_data.append(next((e['count'] for e in month_entries if e['status'] == 'rejected'), 0))

    theses_by_course = list(
        Submission.objects
        .filter(status='approved', approved_at__isnull=False, course__isnull=False)
        .values(course_name=F('course__name'))  # ← This works using the FK relationship
        .annotate(count=Count('id'))
        .order_by('-count')[:16]
    )

    for item in theses_by_course:
        name = item['course_name']

        # Shorten overly long course names
        item['course_name'] = " ".join(name.split()[4:]) if len(name.split()) > 4 else name

    # Analytics: Theses per department
    theses_by_department = list(
        Submission.objects
        .filter(status='approved', approved_at__isnull=False)
        .values('department__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:16]
    )

    for item in theses_by_department:
        name = item['department__name']
        if " - " in name:
            item['department__name'] = name.split(" - ")[0]

    # ✅ Recent Activity - ordered by approval date (most recent first)
    recent_theses = (
        Submission.objects
        .annotate(
            rejected_date=Subquery(
                RejectedThesis.objects.filter(original_submission_id=OuterRef('id')).values('rejected_at')[:1]
            ),
            activity_date=Case(
                When(status='approved', then='approved_at'),
                When(status='rejected', then='rejected_date'),
                default='created_at',
                output_field=DateTimeField(),
            )
        )
        .select_related('submitter', 'department', 'category', 'course')
        .order_by('-activity_date')[:16]
    )

    archive_path = os.path.join(settings.MEDIA_ROOT, 'thesis_files', 'Archived')
    if os.path.exists(archive_path):
        archived_theses_count = len([
            f for f in os.listdir(archive_path)
            if os.path.isfile(os.path.join(archive_path, f))
        ])
    else:
        archived_theses_count = 0

    context = {
        'total_theses': total_theses,
        'total_users': total_users,
        'pending_submissions': pending_submissions,
        'approved_theses': approved_theses,
        'download_logs': download_logs,
        'theses_by_department': theses_by_department,
        'recent_theses': recent_theses,
        'theses_by_course': theses_by_course,
        'months': months,
        'approved_data': approved_data,
        'pending_data': pending_data,
        'rejected_data': rejected_data,
        'archived_theses_count': archived_theses_count,
    }

    return render(request, 'main/admin_dashboard.html', context)

@login_required
def admin_log_entries(request):
    logs = LogEntry.objects.all().select_related('user', 'content_type').order_by('-action_time')
    return render(request, 'main/admin_log_entries.html', {'logs': logs})

@login_required
def user_list(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'main/user_list.html', {'users': users})

@login_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    return redirect('user_list')

@login_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        # Handle password change form
        if 'change_password' in request.POST:
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')


            if new_password != confirm_password:
                messages.error(request, "New passwords do not match.")
                return redirect('edit_user', user_id=user.id)

            user.set_password(new_password)
            user.save()
            messages.success(request, "Password updated successfully.")
            return redirect('user_list')  # ✅ redirect to user list after success

        # Handle user detail updates
        username = request.POST.get('username')
        email = request.POST.get('email')
        role = request.POST.get('role')

        user.username = username
        user.email = email
        user.save()

        # Update profile role
        profile, _ = Profile.objects.get_or_create(user=user)
        if role:
            profile.role = role
            profile.save()
            
            # Synchronize is_staff for admin/librarian if needed
            if role in [Profile.ADMIN, Profile.LIBRARIAN]:
                user.is_staff = True
            else:
                user.is_staff = False
            user.save()

        messages.success(request, "User details updated successfully.")
        return redirect('user_list')  # ✅ redirect here instead of reloading edit page

    return render(request, 'main/edit_user.html', {'user': user})

@csrf_exempt
def change_password(request, user_id):
    if request.method == "POST":
        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({"success": False, "message": "User not found."})

        # ✅ For admins: no need to check old password
        if request.user.is_staff:
            if new_password != confirm_password:
                return JsonResponse({"success": False, "message": "Passwords do not match."})
            user.set_password(new_password)
            user.save()
            return JsonResponse({"success": True, "message": "Password changed successfully (admin override)."})

        # ✅ For normal users
        if not user.check_password(old_password):
            return JsonResponse({"success": False, "message": "Old password is incorrect."})

        if new_password != confirm_password:
            return JsonResponse({"success": False, "message": "Passwords do not match."})

        user.set_password(new_password)
        user.save()
        return JsonResponse({"success": True, "message": "Password changed successfully."})

    return JsonResponse({"success": False, "message": "Invalid request."})

def pending_submissions(request):
    theses = Submission.objects.filter(status='pending').order_by('-created_at')
    return render(request, 'main/pending_submissions.html', {'theses': theses})

@login_required
@user_passes_test(lambda u: u.is_staff)
def approve_thesis(request, thesis_id):
    """Approve a pending submission and move it to the Thesis table, similar to admin bulk approval."""
    submission = get_object_or_404(Submission, id=thesis_id)

    STATUS_PENDING = getattr(Submission, 'STATUS_PENDING', 'pending')
    STATUS_APPROVED = getattr(Submission, 'STATUS_APPROVED', 'approved')

    # If it's already approved, just notify
    if str(submission.status).lower() == STATUS_APPROVED.lower():
        messages.info(request, f"Submission '{submission.title}' is already approved.")
        return redirect('pending_submissions')

    if request.method == 'POST':
        lc_classification = request.POST.get('lc_classification', '').strip()
        
        try:
            submission_title = submission.title

            # Approve via model method (this should create a Thesis record)
            thesis = submission.approve(approved_by=request.user, lc_classification=lc_classification)

            # Remove Django’s automatic log entries
            thesis_ct = ContentType.objects.get_for_model(thesis)
            submission_ct = ContentType.objects.get_for_model(submission)

            LogEntry.objects.filter(
                user=request.user,
                content_type=thesis_ct,
                object_id=thesis.id,
                action_flag=ADDITION
            ).delete()

            LogEntry.objects.filter(
                user=request.user,
                content_type=submission_ct,
                object_id=submission.id,
                action_flag__in=[CHANGE, DELETION]
            ).delete()

            # Log our own admin-style custom action
            log_admin_action(
                request.user,
                thesis,
                ADDITION,
                f"[APPROVED] Submission '{submission_title}' and moved to Thesis table"
            )

            messages.success(
                request,
                f"Submission '{submission_title}' approved successfully and moved to Thesis table."
            )

        except ValueError as e:
            messages.error(request, f"Could not approve '{submission.title}': {str(e)}")

    return redirect('pending_submissions')

def reject_thesis(request, thesis_id):
    # Only staff/admin users can reject theses
    if not request.user.is_staff:
        return HttpResponseForbidden("You are not authorized to perform this action.")

    # Get submission first without status filter to handle already-rejected cases
    submission = get_object_or_404(Submission, id=thesis_id)

    # Handle POST request - process rejection with reason
    if request.method == 'POST':
        # Check if already rejected (prevents double-submit issues)
        if submission.status == Submission.STATUS_REJECTED:
            messages.info(request, f"This submission '{submission.title}' has already been rejected.")
            return redirect('pending_submissions')
        
        # Verify it's still pending
        if submission.status != Submission.STATUS_PENDING:
            messages.error(request, f"Cannot reject submission '{submission.title}'. It is not in pending status.")
            return redirect('pending_submissions')
        
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        
        if not rejection_reason:
            messages.error(request, "Rejection reason is required. Please provide a reason for rejecting this thesis.")
            # Create a simple form object for error display
            class SimpleForm:
                def __init__(self):
                    self.rejection_reason = type('obj', (object,), {'value': '', 'errors': ['This field is required.']})()
            form = SimpleForm()
            return render(request, 'main/reject_thesis.html', {
                'submission': submission,
                'form': form
            })

        try:
            # Store submission title before rejection
            submission_title = submission.title

            # Perform rejection with provided reason
            rejected_thesis = submission.reject(
                rejection_reason=rejection_reason,
                rejected_by=request.user
            )

            # --- Clean up automatic logs ---
            rejected_ct = ContentType.objects.get_for_model(rejected_thesis)
            LogEntry.objects.filter(
                user=request.user,
                content_type=rejected_ct,
                object_id=rejected_thesis.id,
                action_flag=ADDITION
            ).delete()

            submission_ct = ContentType.objects.get_for_model(submission)
            LogEntry.objects.filter(
                user=request.user,
                content_type=submission_ct,
                object_id=submission.id,
                action_flag__in=[CHANGE, DELETION]
            ).delete()

            # --- Custom log entry for rejection ---
            log_admin_action(
                request.user,
                rejected_thesis,
                ADDITION,
                f"[REJECTED] Submission '{submission_title}' - Reason: {rejection_reason[:100]}"
            )

            # Success feedback
            messages.success(request, f"Successfully rejected '{submission_title}'. It has been moved to the Rejected Thesis archive.")

        except ValueError as e:
            messages.error(request, f"Could not reject '{submission.title}': {str(e)}")

        return redirect('pending_submissions')

    # Handle GET request - show rejection form
    # Verify it's still pending for GET requests too
    if submission.status != Submission.STATUS_PENDING:
        if submission.status == Submission.STATUS_REJECTED:
            messages.info(request, f"This submission '{submission.title}' has already been rejected.")
        else:
            messages.error(request, f"Cannot reject submission '{submission.title}'. It is not in pending status.")
        return redirect('pending_submissions')
    
    class SimpleForm:
        def __init__(self):
            self.rejection_reason = type('obj', (object,), {'value': '', 'errors': []})()
    
    form = SimpleForm()
    return render(request, 'main/reject_thesis.html', {
        'submission': submission,
        'form': form
    })


def view_thesis(request, thesis_id):
    """
    Securely views the thesis.
    REPLACED: FileResponse (PDF Downloadable)
    WITH: HTML Viewer (Images Only)
    """
    # 1. Get the object
    try:
        thesis = Thesis.objects.get(pk=thesis_id)
    except Thesis.DoesNotExist:
        thesis = get_object_or_404(Submission, pk=thesis_id)

    # 2. Check Authentication & Permissions (Divide Clear)
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to view this document.")
        return redirect('login')

    # ADMIN and LIBRARIAN have full view, others only abstract
    if request.user.profile.role not in [Profile.ADMIN, Profile.LIBRARIAN]:
        messages.error(request, "Full document access is restricted to Administrators and Librarians. You can only view the abstract.")
        return redirect('thesis_detail', pk=thesis_id)

    # 3. Verify file exists
    if not getattr(thesis, 'file', None) or not os.path.exists(thesis.file.path):
        raise Http404("Thesis file is missing.")

    # 4. Get Page Count
    try:
        doc = fitz.open(thesis.file.path)
        total_pages = doc.page_count
        doc.close()
    except Exception:
        raise Http404("Corrupted PDF file.")

    # 5. Render a Secure Viewer Page
    # This HTML disables right-click and overlays a transparent div to prevent drag-and-drop
    query = request.GET.get('q', '')

    context = {
        'thesis': thesis,
        'total_pages': range(1, total_pages + 1),
        'thesis_id': thesis_id,
        'query': query  # Pass query to template
    }
    return render(request, 'main/secure_viewer.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def rejected_thesis_list(request):
    rejected_theses = RejectedThesis.objects.all()

    # Trim course name safely
    for thesis in rejected_theses:
        course_obj = thesis.course  # this is a Course instance, not a string
        if course_obj:
            # Convert to string (in case Course.__str__() returns full name)
            course_name = str(course_obj)
            if '-' in course_name:
                course_name = course_name.split('-')[0].strip()
            thesis.course_display = course_name
        else:
            thesis.course_display = "N/A"

    return render(request, 'main/rejected_thesis.html', {'rejected_theses': rejected_theses})

@login_required
@user_passes_test(lambda u: u.is_staff)
def theses_list(request):
    theses = Thesis.objects.all()

    # Clean course names before the dash
    for thesis in theses:
        course_obj = thesis.course
        if course_obj:
            course_name = str(course_obj)
            if '-' in course_name:
                course_name = course_name.split('-')[0].strip()
            thesis.course_display = course_name
        else:
            thesis.course_display = "N/A"

    return render(request, 'main/theses.html', {'theses': theses})

@login_required
@user_passes_test(lambda u: u.is_staff)
def departments_list(request):
    departments = Department.objects.annotate(courses_count=Count('courses'))
    return render(request, 'main/departments.html', {'departments': departments})

@login_required
@user_passes_test(lambda u: u.is_staff)
def courses_list(request):
    courses = Course.objects.select_related('department').all()
    return render(request, 'main/courses.html', {'courses': courses})


def admin_categories(request):
    categories = Category.objects.all()

    # Build a list with department and course counts (like in your friend’s admin)
    category_data = []
    for category in categories:
        department_count = category.departments.count()
        course_count = sum(dept.courses.count() for dept in category.departments.all())
        category_data.append({
            'name': category.name,
            'department_count': department_count,
            'course_count': course_count,
        })

    return render(request, 'main/admin_categories.html', {'categories': category_data})


@login_required
@user_passes_test(lambda u: u.is_staff)
def students_list(request):
    """List all students for admin management"""
    students = Student.objects.all().order_by('student_id')
    return render(request, 'main/students_list.html', {'students': students})

def import_students(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)  # <-- read JSON from body
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    students = data.get("students", [])
    created_students = []

    for s in students:
        student_id = s.get("student_id")
        first = s.get("first_name")
        last = s.get("last_name")
        email = s.get("email")

        if not student_id:
            continue

        if not Student.objects.filter(student_id=student_id).exists():
            student = Student.objects.create(
                student_id=student_id,
                first_name=first,
                last_name=last,
                email=email,
                created_at=timezone.now(),
            )
            created_students.append(student)

    # Prepare data to return to JS
    response_students = [
        {
            "student_id": s.student_id,
            "first_name": s.first_name,
            "last_name": s.last_name,
            "email": s.email,
            "created_at": s.created_at.isoformat()
        } for s in created_students
    ]

    return JsonResponse({
        "message": "Imported",
        "count": len(created_students),
        "students": response_students
    })

def import_professors(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)  # Read JSON from request body
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    professors = data.get("professors", [])
    created_professors = []

    for p in professors:
        professor_id = p.get("professor_id")
        first = p.get("first_name")
        last = p.get("last_name")
        email = p.get("email")

        if not professor_id:
            continue

        # Only create if it doesn't already exist
        if not Professor.objects.filter(professor_id=professor_id).exists():
            professor = Professor.objects.create(
                professor_id=professor_id,
                first_name=first,
                last_name=last,
                email=email,
                created_at=timezone.now(),
            )
            created_professors.append(professor)

    # Prepare data to return to JS
    response_professors = [
        {
            "professor_id": p.professor_id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "email": p.email,
            "created_at": p.created_at.isoformat()
        } for p in created_professors
    ]

    return JsonResponse({
        "message": "Imported",
        "count": len(created_professors),
        "professors": response_professors
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def add_student(request):
    if request.method == "POST":
        student_id = request.POST.get("student_id")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")

        Student.objects.create(
            student_id=student_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

        return redirect("students_list")

    return render(request, "main/add_student.html")

@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_student(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    if request.method == "POST":
        student.student_id = request.POST.get("student_id")
        student.first_name = request.POST.get("first_name")
        student.last_name = request.POST.get("last_name")
        student.email = request.POST.get("email")
        student.save()
        return redirect('students_list')
    return render(request, 'main/edit_student.html', {'student': student})

def delete_student(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    student.delete()
    messages.success(request, f"Student {student.student_id} has been deleted.")
    return redirect('students_list')  # adjust if your listing URL name is different

def delete_professor(request, professor_id):
    professor = get_object_or_404(Professor, professor_id=professor_id)
    professor.delete()
    messages.success(request, f"Professor {professor.professor_id} has been deleted.")
    return redirect('professors_list')  # adjust this name to your listing URL

@login_required
@user_passes_test(lambda u: u.is_staff)
def professors_list(request):
    """List all professors for admin management"""
    professors = Professor.objects.all().order_by('professor_id')
    return render(request, 'main/professors_list.html', {'professors': professors})


def add_professor(request):
    if request.method == "POST":
        professor_id = request.POST.get("professor_id")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")

        Professor.objects.create(
            professor_id=professor_id,
            first_name=first_name,
            last_name=last_name,
            email=email
        )
        return redirect('professors_list')

    return render(request, 'main/add_professor.html')


def edit_professor(request, professor_id):
    professor = get_object_or_404(Professor, professor_id=professor_id)

    if request.method == "POST":
        professor.first_name = request.POST.get("first_name")
        professor.last_name = request.POST.get("last_name")
        professor.email = request.POST.get("email")
        professor.save()
        return redirect('professors_list')

    return render(request, 'main/edit_professor.html', {'professor': professor})


@login_required
@require_POST
def create_submission(request):
    title = request.POST.get('thesisTitle') or request.POST.get('title')
    abstract = request.POST.get('abstract', '')
    keywords = request.POST.get('keywords', '')
    research_category = request.POST.get('research_category', '')
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
        print(f"Submission validation errors: {errors}")
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

        # Extract title from PDF if not provided
        if not title or title.strip() == '':
            if thesis_file:
                try:
                    # The extract_title_from_pdf function handles file reading internally
                    # and creates a temporary copy, so the original file remains intact
                    extracted_title = extract_title_from_pdf(thesis_file)
                    if extracted_title:
                        title = extracted_title
                except Exception as e:
                    # If extraction fails, continue with empty title
                    print(f"Warning: Could not extract title from PDF: {str(e)}")
        
        # Extract abstract from PDF if not provided
        if not abstract or abstract.strip() == '':
            if thesis_file:
                try:
                    # The extract_abstract_from_pdf function handles file reading internally
                    # and creates a temporary copy, so the original file remains intact
                    extracted_abstract = extract_abstract_from_pdf(thesis_file)
                    if extracted_abstract:
                        abstract = extracted_abstract
                except Exception as e:
                    # If extraction fails, continue with empty abstract
                    print(f"Warning: Could not extract abstract from PDF: {str(e)}")

        submission = Submission.objects.create(
            submitter=request.user,
            title=title.strip(),
            author=f"{request.POST.get('firstName', '').strip()} {request.POST.get('lastName', '').strip()}".strip(),
            year=int(year) if year and str(year).isdigit() else None,
            abstract=abstract,
            keywords=keywords,
            research_category=research_category,
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
        import traceback
        print(f"EXCEPTION in create_submission: {str(e)}")
        print(traceback.format_exc())
        messages.error(request, f'Error submitting thesis: {str(e)}')
        return redirect('student_dashboard')


@login_required
def my_submissions(request):
    submissions = Submission.objects.filter(submitter=request.user)
    return render(request, 'main/my_submissions.html', {'submissions': submissions})


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


def view_thesis_file(request, pk):
    thesis = get_object_or_404(Thesis, pk=pk)
    if not thesis.file:
        raise Http404('File not found.')

    # For non-authenticated users, serve restricted preview
    if not request.user.is_authenticated:
        return restricted_view_thesis_file(request, pk)

    # For authenticated users, check role
    if request.user.profile.role not in [Profile.ADMIN, Profile.LIBRARIAN]:
        return HttpResponseForbidden("Access restricted to abstract only for your account type.")

    response = FileResponse(thesis.file.open('rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(thesis.file.name)}"'
    return response


def view_thesis_file_highlight(request, pk):
    """Render a temporary PDF with highlighted query occurrences and optional page jump."""
    thesis = get_object_or_404(Thesis, pk=pk)
    if not thesis.file:
        raise Http404('File not found.')

    # Check permissions
    if request.user.is_authenticated and request.user.profile.role not in [Profile.ADMIN, Profile.LIBRARIAN]:
        return HttpResponseForbidden("Access restricted to abstract only for your account type.")
    
    query = (request.GET.get('q') or '').strip()
    if not query:
        # Fallback to normal viewing if no query supplied
        return view_thesis_file(request, pk)

    try:
        # Resolve file path
        try:
            pdf_path = thesis.file.path
        except Exception:
            from django.conf import settings
            pdf_path = os.path.join(settings.MEDIA_ROOT, thesis.file.name)

        doc = fitz.open(pdf_path)
        query_lower = query.lower()
        first_hit_page_index = None
        highlight_count = 0

        # Highlight on each page using text search rectangles
        for page_index in range(doc.page_count):
            page = doc[page_index]
            text_instances = page.search_for(query)
            # If nothing, try a simple regex-like approach by words
            if not text_instances and len(query.split()) > 1:
                # Try each token to increase chance of visibility
                for token in query.split():
                    text_instances.extend(page.search_for(token))
            if text_instances:
                if first_hit_page_index is None:
                    first_hit_page_index = page_index
                for rect in text_instances:
                    annot = page.add_highlight_annot(rect)
                    if annot:
                        annot.update()
                        highlight_count += 1

        # Stream the modified document
        output_buffer = io.BytesIO()
        doc.save(output_buffer)
        doc.close()
        output_buffer.seek(0)

        response = HttpResponse(output_buffer.getvalue(), content_type='application/pdf')
        safe_name = os.path.basename(thesis.file.name)
        response['Content-Disposition'] = f'inline; filename="highlight_{safe_name}"'
        # Include X-Info about highlights for potential frontend telemetry
        response['X-Highlights'] = str(highlight_count)
        return response

    except Exception as e:
        return HttpResponse(f"Error highlighting PDF: {str(e)}", status=500)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def download_thesis_file(request, pk):
    """
    Strictly forbids downloading.
    """
    # Log the attempt if necessary
    if request.user.is_authenticated:
        print(f"Security Alert: User {request.user.username} attempted to download thesis {pk}")

    return HttpResponseForbidden(
        "Security Policy: Downloading thesis documents is strictly prohibited. Intellectual Property Protection Active.")


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
            p.drawString(100, 550, "Please log in to view the complete thesis.")
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

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))


def send_verification_email(user, code):
    """Send verification code to user's email"""
    subject = 'Thesis Library - Email Verification Code'
    message = f'''
Hello {user.username},

Thank you for signing up for Thesis Library!

Your verification code is: {code}

This code will expire in 24 hours.

If you did not create this account, please ignore this email.

Best regards,
Thesis Library Team
'''
    try:
        send_mail(
            subject,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@thesislibrary.com'),
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


def send_password_reset_email(user, code):
    """Send password reset code to user's email"""
    subject = 'Thesis Library - Password Reset Code'
    message = f'''
Hello {user.username},

You requested to reset your password for Thesis Library.

Your password reset code is: {code}

This code will expire in 1 hour.

If you did not request this password reset, please ignore this email and your password will remain unchanged.

Best regards,
Thesis Library Team
'''
    try:
        send_mail(
            subject,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@thesislibrary.com'),
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


@csrf_protect
def login_view(request):
    """Handle login with ID as username - only verified accounts can login"""
    if request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                user_id = data.get('username')  # This is actually the ID
                password = data.get('password')
                
                if not user_id or not password:
                    return JsonResponse({'success': False, 'error': 'ID and password are required'}, status=400)
                
                # Authenticate using ID as username
                user = authenticate(request, username=user_id, password=password)
                
                if user:
                    # Check if account is active and verified
                    if not user.is_active:
                        return JsonResponse({'success': False, 'error': 'Your account is inactive. Please verify your email first.'}, status=400)
                    
                    # Check if user has been verified
                    try:
                        verification = VerificationCode.objects.get(user=user)
                        if not verification.is_verified:
                            return JsonResponse({'success': False, 'error': 'Please verify your email before logging in. Check your email for the verification code.'}, status=400)
                    except VerificationCode.DoesNotExist:
                        # If no verification code exists, account might be old - allow login if active
                        pass
                    
                    login(request, user)
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False, 'error': 'Invalid ID or password'}, status=400)
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
        else:
            # Form POST
            user_id = request.POST.get('username')  # This is actually the ID
            password = request.POST.get('password')
            
            if not user_id or not password:
                errors = {'__all__': ['ID and password are required']}
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'errors': errors})
                else:
                    messages.error(request, 'ID and password are required.')
                    return redirect('/')
            
            user = authenticate(request, username=user_id, password=password)
            
            if user:
                # Check if account is active and verified
                if not user.is_active:
                    errors = {'__all__': ['Your account is inactive. Please verify your email first.']}
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'errors': errors})
                    else:
                        messages.error(request, 'Your account is inactive. Please verify your email first.')
                        return redirect('/')
                
                # Check if user has been verified
                try:
                    verification = VerificationCode.objects.get(user=user)
                    if not verification.is_verified:
                        errors = {'__all__': ['Please verify your email before logging in. Check your email for the verification code.']}
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'success': False, 'errors': errors})
                        else:
                            messages.error(request, 'Please verify your email before logging in.')
                            return redirect('/')
                except VerificationCode.DoesNotExist:
                    pass
                
                login(request, user)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    next_url = request.POST.get('next') or request.GET.get('next') or '/'
                    return JsonResponse({'success': True, 'redirect_url': next_url})
                else:
                    next_url = request.POST.get('next') or request.GET.get('next') or '/'
                    return redirect(next_url)
            else:
                errors = {'__all__': ['Invalid ID or password']}
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'errors': errors})
                else:
                    messages.error(request, 'Invalid ID or password.')
                    return redirect('/')
    return redirect('/')


@csrf_exempt
def signup_view(request):
    """Handle signup with ID verification - checks Student/Professor DB"""
    if request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                user_id = data.get("id") or data.get("username")  # Accept both 'id' and 'username'
                email = data.get("email")
                password = data.get("password")
                
                if not user_id or not password or not email:
                    return JsonResponse({"success": False, "error": "ID, email, and password are required"}, status=400)
                
                # Check if ID exists in Student or Professor database
                student = None
                professor = None
                student_exists = False
                professor_exists = False
                
                try:
                    student = Student.objects.get(student_id=user_id)
                    student_exists = True
                except Student.DoesNotExist:
                    pass
                
                try:
                    professor = Professor.objects.get(professor_id=user_id)
                    professor_exists = True
                except Professor.DoesNotExist:
                    pass
                
                if not student_exists and not professor_exists:
                    return JsonResponse({"success": False, "error": "ID not found in our database. Please contact administrator."}, status=400)
                
                # Get official email from Student/Professor record
                official_email = None
                official_email_original = None
                if student_exists and student.email:
                    official_email_original = student.email.strip()
                    official_email = official_email_original.lower()
                elif professor_exists and professor.email:
                    official_email_original = professor.email.strip()
                    official_email = official_email_original.lower()
                
                # Validate that the entered email matches the official email for this ID
                if official_email:
                    # If official email exists in database, user must enter the exact same email (case-insensitive)
                    if email.strip().lower() != official_email:
                        return JsonResponse({
                            "success": False, 
                            "error": f"The email you entered does not match the email on file for ID {user_id}. Please use the correct email address."
                        }, status=400)
                    final_email = official_email_original
                else:
                    # If no official email in database, use the email they entered
                    # But check if this email is already associated with a different ID
                    email_lower = email.strip().lower()
                    # Check if this email is associated with another student/professor
                    conflicting_student = Student.objects.filter(email__iexact=email_lower).exclude(student_id=user_id).first()
                    conflicting_professor = Professor.objects.filter(email__iexact=email_lower).exclude(professor_id=user_id).first()
                    
                    if conflicting_student:
                        return JsonResponse({
                            "success": False,
                            "error": f"This email is already associated with Student ID {conflicting_student.student_id}. Please use the correct email for your ID."
                        }, status=400)
                    
                    if conflicting_professor:
                        return JsonResponse({
                            "success": False,
                            "error": f"This email is already associated with Professor ID {conflicting_professor.professor_id}. Please use the correct email for your ID."
                        }, status=400)
                    
                    final_email = email.strip()
                
                # Check if user already exists
                existing_user = None
                try:
                    existing_user = User.objects.get(username=user_id)
                except User.DoesNotExist:
                    pass
                
                if existing_user:
                    # User already exists - check if verified
                    try:
                        verification = VerificationCode.objects.get(user=existing_user)
                        if verification.is_verified:
                            # Account is already verified - tell them to log in
                            return JsonResponse({
                                "success": False, 
                                "error": "An account with this ID already exists and is verified. Please log in instead."
                            }, status=400)
                        else:
                            # Account exists but not verified - resend verification code
                            # Update password if provided
                            if password:
                                existing_user.set_password(password)
                                existing_user.save()
                            
                            # Update email if it's different
                            if existing_user.email != final_email:
                                existing_user.email = final_email
                                existing_user.save()
                            
                            # Generate new verification code
                            code = generate_verification_code()
                            expires_at = timezone.now() + timezone.timedelta(hours=getattr(settings, 'VERIFICATION_CODE_EXPIRY_HOURS', 24))
                            
                            # Update or create verification code
                            verification.code = code
                            verification.expires_at = expires_at
                            verification.is_verified = False
                            verification.save()
                            
                            # Resend verification email
                            email_sent = send_verification_email(existing_user, code)
                            
                            if email_sent:
                                return JsonResponse({
                                    "success": True,
                                    "message": f"Verification code has been resent to {final_email}. Please check your email.",
                                    "requires_verification": True,
                                    "email_sent_to": final_email,
                                    "resend": True
                                })
                            else:
                                return JsonResponse({
                                    "success": False,
                                    "error": "Failed to resend verification email. Please contact support."
                                }, status=500)
                    except VerificationCode.DoesNotExist:
                        # User exists but no verification code - create one
                        code = generate_verification_code()
                        expires_at = timezone.now() + timezone.timedelta(hours=getattr(settings, 'VERIFICATION_CODE_EXPIRY_HOURS', 24))
                        VerificationCode.objects.create(
                            user=existing_user,
                            code=code,
                            expires_at=expires_at
                        )
                        
                        # Update password and email
                        if password:
                            existing_user.set_password(password)
                        existing_user.email = final_email
                        existing_user.is_active = False
                        if professor_exists:
                            existing_user.is_staff = True
                        existing_user.save()
                        
                        email_sent = send_verification_email(existing_user, code)
                        
                        if email_sent:
                            return JsonResponse({
                                "success": True,
                                "message": f"Verification code has been sent to {final_email}. Please check your email.",
                                "requires_verification": True,
                                "email_sent_to": final_email
                            })
                        else:
                            return JsonResponse({
                                "success": False,
                                "error": "Failed to send verification email. Please contact support."
                            }, status=500)
                
                # Check if email is already in use by a different user
                if User.objects.filter(email=final_email).exclude(username=user_id).exists():
                    return JsonResponse({"success": False, "error": "This email is already registered with a different account"}, status=400)
                
                # Create new inactive user account
                user = User.objects.create_user(
                    username=user_id,
                    email=final_email,
                    password=password,
                    is_active=False  # Account is inactive until verified
                )
                
                # Set user role based on ID type
                if professor_exists:
                    user.profile.role = Profile.PROFESSOR
                    user.profile.save()
                
                # Generate verification code
                code = generate_verification_code()
                expires_at = timezone.now() + timezone.timedelta(hours=getattr(settings, 'VERIFICATION_CODE_EXPIRY_HOURS', 24))
                
                # Create verification code record
                VerificationCode.objects.create(
                    user=user,
                    code=code,
                    expires_at=expires_at
                )
                
                # Automatically send verification email to the email address (from DB or entered)
                email_sent = send_verification_email(user, code)
                
                if email_sent:
                    email_message = f"Account created! Verification code has been automatically sent to {final_email}."
                    return JsonResponse({
                        "success": True, 
                        "message": email_message,
                        "requires_verification": True,
                        "email_sent_to": final_email
                    })
                else:
                    return JsonResponse({
                        "success": False, 
                        "error": "Account created but failed to send verification email. Please contact support."
                    }, status=500)

            except Exception as e:
                return JsonResponse({"success": False, "error": str(e)}, status=500)
        else:
            # Form POST
            user_id = request.POST.get('id') or request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            
            if not user_id or not email or not password:
                errors = {'__all__': ['ID, email, and password are required']}
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'errors': errors})
                else:
                    messages.error(request, 'ID, email, and password are required.')
                    return redirect('/')
            
            # Check if ID exists in Student or Professor database
            student = None
            professor = None
            student_exists = False
            professor_exists = False
            
            try:
                student = Student.objects.get(student_id=user_id)
                student_exists = True
            except Student.DoesNotExist:
                pass
            
            try:
                professor = Professor.objects.get(professor_id=user_id)
                professor_exists = True
            except Professor.DoesNotExist:
                pass
            
            if not student_exists and not professor_exists:
                errors = {'__all__': ['ID not found in our database. Please contact administrator.']}
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'errors': errors})
                else:
                    messages.error(request, 'ID not found in our database.')
                    return redirect('/')
            
            # Get official email from Student/Professor record
            official_email = None
            official_email_original = None
            if student_exists and student.email:
                official_email_original = student.email.strip()
                official_email = official_email_original.lower()
            elif professor_exists and professor.email:
                official_email_original = professor.email.strip()
                official_email = official_email_original.lower()
            
            # Validate that the entered email matches the official email for this ID
            if official_email:
                # If official email exists in database, user must enter the exact same email (case-insensitive)
                if email.strip().lower() != official_email:
                    error_msg = f'The email you entered does not match the email on file for ID {user_id}. Please use the correct email address.'
                    errors = {'__all__': [error_msg]}
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'errors': errors})
                    else:
                        messages.error(request, error_msg)
                        return redirect('/')
                final_email = official_email_original
            else:
                # If no official email in database, use the email they entered
                # But check if this email is already associated with a different ID
                email_lower = email.strip().lower()
                # Check if this email is associated with another student/professor
                conflicting_student = Student.objects.filter(email__iexact=email_lower).exclude(student_id=user_id).first()
                conflicting_professor = Professor.objects.filter(email__iexact=email_lower).exclude(professor_id=user_id).first()
                
                if conflicting_student:
                    error_msg = f'This email is already associated with Student ID {conflicting_student.student_id}. Please use the correct email for your ID.'
                    errors = {'__all__': [error_msg]}
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'errors': errors})
                    else:
                        messages.error(request, error_msg)
                        return redirect('/')
                
                if conflicting_professor:
                    error_msg = f'This email is already associated with Professor ID {conflicting_professor.professor_id}. Please use the correct email for your ID.'
                    errors = {'__all__': [error_msg]}
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'errors': errors})
                    else:
                        messages.error(request, error_msg)
                        return redirect('/')
                
                final_email = email.strip()
            
            # Check if user already exists
            existing_user = None
            try:
                existing_user = User.objects.get(username=user_id)
            except User.DoesNotExist:
                pass
            
            if existing_user:
                # User already exists - check if verified
                try:
                    verification = VerificationCode.objects.get(user=existing_user)
                    if verification.is_verified:
                        # Account is already verified
                        errors = {'__all__': ['An account with this ID already exists and is verified. Please log in instead.']}
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'success': False, 'errors': errors})
                        else:
                            messages.error(request, 'An account with this ID already exists and is verified. Please log in instead.')
                            return redirect('/')
                    else:
                        # Account exists but not verified - resend verification code
                        if password:
                            existing_user.set_password(password)
                            existing_user.save()
                        
                        if existing_user.email != final_email:
                            existing_user.email = final_email
                            existing_user.save()
                        
                        code = generate_verification_code()
                        expires_at = timezone.now() + timezone.timedelta(hours=getattr(settings, 'VERIFICATION_CODE_EXPIRY_HOURS', 24))
                        verification.code = code
                        verification.expires_at = expires_at
                        verification.is_verified = False
                        verification.save()
                        
                        email_sent = send_verification_email(existing_user, code)
                        email_message = f"Verification code has been resent to {final_email}. Please check your email."
                        
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({
                                'success': True,
                                'message': email_message,
                                'requires_verification': True,
                                'email_sent_to': final_email,
                                'resend': True
                            })
                        else:
                            messages.success(request, email_message)
                            return redirect('/')
                except VerificationCode.DoesNotExist:
                    # User exists but no verification code - create one
                    code = generate_verification_code()
                    expires_at = timezone.now() + timezone.timedelta(hours=getattr(settings, 'VERIFICATION_CODE_EXPIRY_HOURS', 24))
                    VerificationCode.objects.create(
                        user=existing_user,
                        code=code,
                        expires_at=expires_at
                    )
                    
                    if password:
                        existing_user.set_password(password)
                    existing_user.email = final_email
                    existing_user.is_active = False
                    if professor_exists:
                        existing_user.is_staff = True
                    existing_user.save()
                    
                    email_sent = send_verification_email(existing_user, code)
                    email_message = f"Verification code has been sent to {final_email}. Please check your email."
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': email_message,
                            'requires_verification': True,
                            'email_sent_to': final_email
                        })
                    else:
                        messages.success(request, email_message)
                        return redirect('/')
            
            # Check if email is already in use by a different user
            if User.objects.filter(email=final_email).exclude(username=user_id).exists():
                errors = {'__all__': ['This email is already registered with a different account']}
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'errors': errors})
                else:
                    messages.error(request, 'This email is already registered with a different account.')
                    return redirect('/')
            
            # Create new inactive user
            user = User.objects.create_user(
                username=user_id,
                email=final_email,
                password=password,
                is_active=False
            )
            
            if professor_exists:
                user.profile.role = Profile.PROFESSOR
                user.profile.save()
            
            # Generate and automatically send verification code
            code = generate_verification_code()
            expires_at = timezone.now() + timezone.timedelta(hours=getattr(settings, 'VERIFICATION_CODE_EXPIRY_HOURS', 24))
            VerificationCode.objects.create(user=user, code=code, expires_at=expires_at)
            email_sent = send_verification_email(user, code)
            
            email_message = f"Account created! Verification code has been automatically sent to {final_email}."
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'message': email_message,
                    'requires_verification': True,
                    'email_sent_to': final_email
                })
            else:
                messages.success(request, email_message)
                return redirect('/')
    
    return JsonResponse({"success": False, "error": "Invalid request"}, status=400)


@csrf_protect
def verify_email_view(request):
    """Handle email verification with code"""
    if request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                user_id = data.get('id') or data.get('username')
                code = data.get('code')
                
                if not user_id or not code:
                    return JsonResponse({'success': False, 'error': 'ID and verification code are required'}, status=400)
                
                try:
                    user = User.objects.get(username=user_id)
                except User.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
                
                try:
                    verification = VerificationCode.objects.get(user=user)
                    
                    if verification.is_verified:
                        return JsonResponse({'success': False, 'error': 'Email already verified'}, status=400)
                    
                    if verification.is_expired():
                        return JsonResponse({'success': False, 'error': 'Verification code has expired. Please request a new one.'}, status=400)
                    
                    if verification.code != code:
                        return JsonResponse({'success': False, 'error': 'Invalid verification code'}, status=400)
                    
                    # Verify the account
                    verification.is_verified = True
                    verification.save()
                    user.is_active = True
                    user.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Email verified successfully! You can now log in.'
                    })
                    
                except VerificationCode.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'No verification code found for this account'}, status=404)
                    
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
        else:
            # Form POST
            user_id = request.POST.get('id') or request.POST.get('username')
            code = request.POST.get('code')
            
            if not user_id or not code:
                messages.error(request, 'ID and verification code are required.')
                return redirect('/')
            
            try:
                user = User.objects.get(username=user_id)
                verification = VerificationCode.objects.get(user=user)
                
                if verification.is_verified:
                    messages.info(request, 'Email already verified.')
                    return redirect('/')
                
                if verification.is_expired():
                    messages.error(request, 'Verification code has expired.')
                    return redirect('/')
                
                if verification.code != code:
                    messages.error(request, 'Invalid verification code.')
                    return redirect('/')
                
                verification.is_verified = True
                verification.save()
                user.is_active = True
                user.save()
                
                messages.success(request, 'Email verified successfully! You can now log in.')
                return redirect('/')
                
            except (User.DoesNotExist, VerificationCode.DoesNotExist):
                messages.error(request, 'Invalid verification request.')
                return redirect('/')
    
    return redirect('/')


@csrf_protect
def forgot_password(request):
    """Handle forgot password request - send reset code to email"""
    if request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                user_id = data.get('id') or data.get('username')
                email = data.get('email')
                
                if not user_id or not email:
                    return JsonResponse({'success': False, 'error': 'ID and email are required'}, status=400)
                
                try:
                    user = User.objects.get(username=user_id, email=email)
                except User.DoesNotExist:
                    # Don't reveal if user exists or not for security
                    return JsonResponse({
                        'success': True,
                        'message': 'If an account exists with this ID and email, a password reset code has been sent.'
                    })
                
                # Generate reset code
                code = generate_verification_code()
                expires_at = timezone.now() + timezone.timedelta(hours=1)
                
                # Create or update reset code
                PasswordResetCode.objects.filter(user=user, is_used=False).update(is_used=True)
                PasswordResetCode.objects.create(
                    user=user,
                    code=code,
                    expires_at=expires_at
                )
                
                # Send email
                email_sent = send_password_reset_email(user, code)
                
                return JsonResponse({
                    'success': True,
                    'message': 'Password reset code has been sent to your email.'
                })
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
        else:
            # Form POST (could be AJAX with FormData)
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            user_id = request.POST.get('id') or request.POST.get('username')
            email = request.POST.get('email')
            
            if not user_id or not email:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': 'ID and email are required'}, status=400)
                messages.error(request, 'ID and email are required.')
                return redirect('/')
            
            try:
                user = User.objects.get(username=user_id, email=email)
                
                # Generate reset code
                code = generate_verification_code()
                expires_at = timezone.now() + timezone.timedelta(hours=1)
                
                # Create or update reset code
                PasswordResetCode.objects.filter(user=user, is_used=False).update(is_used=True)
                PasswordResetCode.objects.create(
                    user=user,
                    code=code,
                    expires_at=expires_at
                )
                
                # Send email
                email_sent = send_password_reset_email(user, code)
                
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': 'Password reset code has been sent to your email.'
                    })
                messages.success(request, 'Password reset code has been sent to your email.')
                
            except User.DoesNotExist:
                # Don't reveal if user exists or not
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': 'If an account exists with this ID and email, a password reset code has been sent.'
                    })
                messages.success(request, 'If an account exists with this ID and email, a password reset code has been sent.')
            except Exception as e:
                if is_ajax:
                    return JsonResponse({'success': False, 'error': str(e)}, status=500)
                messages.error(request, f'An error occurred: {str(e)}')
            
            if not is_ajax:
                return redirect('/')
    
    return redirect('/')


@csrf_protect
def reset_password(request):
    """Handle password reset with code"""
    if request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                user_id = data.get('id') or data.get('username')
                code = data.get('code')
                new_password = data.get('new_password')
                confirm_password = data.get('confirm_password')
                
                if not user_id or not code or not new_password or not confirm_password:
                    return JsonResponse({'success': False, 'error': 'All fields are required'}, status=400)
                
                if new_password != confirm_password:
                    return JsonResponse({'success': False, 'error': 'Passwords do not match'}, status=400)
                
                try:
                    user = User.objects.get(username=user_id)
                except User.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'User not found'}, status=404)
                
                # Get the most recent unused reset code
                try:
                    reset_code = PasswordResetCode.objects.filter(
                        user=user,
                        is_used=False
                    ).order_by('-created_at').first()
                    
                    if not reset_code:
                        return JsonResponse({'success': False, 'error': 'No valid reset code found. Please request a new one.'}, status=400)
                    
                    if reset_code.is_expired():
                        return JsonResponse({'success': False, 'error': 'Reset code has expired. Please request a new one.'}, status=400)
                    
                    if reset_code.code != code:
                        return JsonResponse({'success': False, 'error': 'Invalid reset code'}, status=400)
                    
                    # Reset password
                    user.set_password(new_password)
                    user.save()
                    
                    # Mark code as used
                    reset_code.is_used = True
                    reset_code.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Password reset successfully! You can now log in with your new password.'
                    })
                    
                except Exception as e:
                    return JsonResponse({'success': False, 'error': str(e)}, status=500)
                    
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
        else:
            # Form POST
            user_id = request.POST.get('id') or request.POST.get('username')
            code = request.POST.get('code')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not user_id or not code or not new_password or not confirm_password:
                messages.error(request, 'All fields are required.')
                return redirect('/')
            
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return redirect('/')
            
            try:
                user = User.objects.get(username=user_id)
                
                # Get the most recent unused reset code
                reset_code = PasswordResetCode.objects.filter(
                    user=user,
                    is_used=False
                ).order_by('-created_at').first()
                
                if not reset_code:
                    messages.error(request, 'No valid reset code found. Please request a new one.')
                    return redirect('/')
                
                if reset_code.is_expired():
                    messages.error(request, 'Reset code has expired. Please request a new one.')
                    return redirect('/')
                
                if reset_code.code != code:
                    messages.error(request, 'Invalid reset code.')
                    return redirect('/')
                
                # Reset password
                user.set_password(new_password)
                user.save()
                
                # Mark code as used
                reset_code.is_used = True
                reset_code.save()
                
                messages.success(request, 'Password reset successfully! You can now log in with your new password.')
                return redirect('/')
                
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
            except Exception as e:
                messages.error(request, f'An error occurred: {str(e)}')
            
            return redirect('/')
    
    return redirect('/')


@login_required
def change_password_profile(request):
    """Handle password change for logged-in users from profile"""
    if request.method == 'POST':
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                old_password = data.get('old_password')
                new_password = data.get('new_password')
                confirm_password = data.get('confirm_password')
                
                if not old_password or not new_password or not confirm_password:
                    return JsonResponse({'success': False, 'error': 'All fields are required'}, status=400)
                
                if new_password != confirm_password:
                    return JsonResponse({'success': False, 'error': 'New passwords do not match'}, status=400)
                
                user = request.user
                
                if not user.check_password(old_password):
                    return JsonResponse({'success': False, 'error': 'Current password is incorrect'}, status=400)
                
                user.set_password(new_password)
                user.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Password changed successfully!'
                })
                
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
        else:
            # Form POST
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not old_password or not new_password or not confirm_password:
                messages.error(request, 'All fields are required.')
                return redirect('profile_card')
            
            if new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
                return redirect('profile_card')
            
            user = request.user
            
            if not user.check_password(old_password):
                messages.error(request, 'Current password is incorrect.')
                return redirect('profile_card')
            
            user.set_password(new_password)
            user.save()
            
            messages.success(request, 'Password changed successfully!')
            return redirect('profile_card')
    
    return redirect('profile_card')


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


@login_required
@require_POST
def api_extract_abstract(request):
    """Extract abstract from uploaded PDF file"""
    try:
        if 'pdf_file' not in request.FILES:
            return JsonResponse({'error': 'No PDF file provided'}, status=400)
        
        pdf_file = request.FILES['pdf_file']
        
        # Validate file type
        if not pdf_file.name.lower().endswith('.pdf'):
            return JsonResponse({'error': 'File must be a PDF'}, status=400)
        
        # Validate file size (max 50MB)
        if pdf_file.size > 50 * 1024 * 1024:
            return JsonResponse({'error': 'File size exceeds 50MB limit'}, status=400)
        
        # Extract abstract and title
        abstract = extract_abstract_from_pdf(pdf_file)
        title = extract_title_from_pdf(pdf_file)
        
        if abstract or title:
            response_data = {
                'success': True,
                'abstract': abstract,
                'title': title
            }
            if abstract:
                response_data['word_count'] = len(abstract.split())
            return JsonResponse(response_data)
        else:
            return JsonResponse({
                'success': False,
                'abstract': '',
                'title': '',
                'message': 'Could not extract abstract or title from PDF. Please enter them manually.'
            })
            
    except Exception as e:
        return JsonResponse({'error': f'Error extracting abstract: {str(e)}'}, status=500)


def csrf_failure(request, reason=""):
    return render(request, "errors/csrf_failure.html", status=403)


# ----------------------
# Secure Image Serving (IPP)
# ----------------------
@login_required
def serve_thesis_page_image(request, thesis_id, page_num):
    """
    Serves a page as an image with IPP (Intellectual Property Protection):
    1. Highlights search terms (if any).
    2. Applies a Watermark logo.
    3. Renders as a flat PNG.
    """
    try:
        # Try to find the thesis in Thesis or Submission
        try:
            thesis = Thesis.objects.get(pk=thesis_id)
        except Thesis.DoesNotExist:
            thesis = get_object_or_404(Submission, pk=thesis_id)

        if not thesis.file or not os.path.exists(thesis.file.path):
            raise Http404("File not found")

        doc = fitz.open(thesis.file.path)

        # Validate page number
        page_index = int(page_num) - 1
        if page_index < 0 or page_index >= doc.page_count:
            raise Http404("Page not found")

        page = doc.load_page(page_index)

        # -------------------------------
        # 1. SEARCH HIGHLIGHTING LOGIC
        # -------------------------------
        search_query = request.GET.get('q', '').strip()
        if search_query:
            text_instances = page.search_for(search_query, quads=True)
            for quad in text_instances:
                highlight = page.add_highlight_annot(quad)
                highlight.set_colors(stroke=[1, 1, 0])  # Yellow color
                highlight.update()

        # -------------------------------
        # 2. WATERMARK LOGIC (NEW)
        # -------------------------------
        # Construct path: BASE_DIR/assets/images/watermark.png
        # Adjust 'watermark.png' if your file has a different extension
        watermark_path = os.path.join(settings.BASE_DIR, 'assets', 'images', 'watermark.png')

        if os.path.exists(watermark_path):
            # Insert the image into the center of the page
            # overlay=True puts it ON TOP of text (prevents OCR/Screenshots)
            # overlay=False puts it BEHIND text
            page.insert_image(
                page.rect,  # Fill the page area (it will center itself)
                filename=watermark_path,
                keep_proportion=True,  # Don't stretch the logo
                overlay=False  # Put on top of text?
            )
        else:
            # Optional: Print to console if watermark is missing so you know to fix the path
            print(f"Warning: Watermark not found at {watermark_path}")

        # -------------------------------
        # 3. RENDER TO IMAGE
        # -------------------------------
        # zoom_x and zoom_y=2.0 creates high-res images (approx 200 DPI)
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)

        response = HttpResponse(pix.tobytes("png"), content_type="image/png")
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        doc.close()
        return response

    except Exception as e:
        print(f"Error serving page: {e}")
        raise Http404