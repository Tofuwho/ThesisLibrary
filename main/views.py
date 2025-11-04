from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q, OuterRef, Subquery
from django.db.models import Value, IntegerField, Case, When, F, ExpressionWrapper, CharField, DateTimeField
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.db.models.functions import Cast, TruncMonth
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.http import FileResponse, Http404, JsonResponse, HttpResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django import forms
from .models import Thesis, Category, Submission, DownloadLog, RejectedThesis, Course, Department
from .utils import search_in_thesis_pdf, suggest_query_correction, deep_filter_theses_by_pdf, get_thesis_preview
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
        theses = theses.distinct()

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
@user_passes_test(lambda u: u.is_staff)  # Only allow admin/staff users
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

        user.username = username
        user.email = email
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
    theses = Submission.objects.filter(status='Pending').order_by('-created_at')
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

    try:
        submission_title = submission.title

        # Approve via model method (this should create a Thesis record)
        thesis = submission.approve(approved_by=request.user)

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

    submission = get_object_or_404(Submission, id=thesis_id, status=Submission.STATUS_PENDING)

    try:
        # Store submission title before rejection
        submission_title = submission.title

        # Perform rejection
        rejected_thesis = submission.reject(
            rejection_reason="Rejected via admin action",
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
            f"[REJECTED] Submission '{submission_title}' and moved to Rejected Thesis archive"
        )

        # Success feedback
        messages.success(request, f"Successfully rejected '{submission_title}'. It has been moved to the Rejected Thesis archive.")

    except ValueError as e:
        messages.error(request, f"Could not reject '{submission.title}': {str(e)}")

    return redirect('pending_submissions.html')  # Change this redirect to wherever your admin dashboard lives

def view_thesis(request, thesis_id):
    """
    Displays or streams the thesis PDF file.
    Works for both Thesis and Submission models.
    Falls back to restricted version if not logged in.
    """
    # Try to find the thesis in the Thesis table first
    try:
        thesis = Thesis.objects.get(pk=thesis_id)
    except Thesis.DoesNotExist:
        # Fallback: maybe it's still a pending submission
        thesis = get_object_or_404(Submission, pk=thesis_id)

    # If it has no file attached
    if not getattr(thesis, 'file', None):
        raise Http404("File not found for this thesis.")

    # If file field exists but is empty or missing in storage
    if not thesis.file.name or not thesis.file.storage.exists(thesis.file.name):
        raise Http404("Thesis file is missing or unavailable.")

    # If the user isn't authenticated → use restricted view
    if not request.user.is_authenticated:
        # Optional: redirect to a limited PDF generator view
        # or just render a restricted notice
        return restricted_view_thesis_file(request, thesis_id)

    # Serve the file as inline PDF (opens in browser)
    response = FileResponse(
        thesis.file.open('rb'),
        content_type='application/pdf'
    )
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(thesis.file.name)}"'
    return response

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

def departments_list(request):
    departments = Department.objects.annotate(courses_count=Count('courses'))
    return render(request, 'main/departments.html', {'departments': departments})

def courses_list(request):
    courses = Course.objects.select_related('department').all()
    return render(request, 'main/courses.html', {'courses': courses})

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


def view_thesis_file_highlight(request, pk):
    """Render a temporary PDF with highlighted query occurrences and optional page jump."""
    thesis = get_object_or_404(Thesis, pk=pk)
    if not thesis.file:
        raise Http404('File not found.')

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
