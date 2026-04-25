import os
import shutil
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q, F, Subquery, OuterRef, DateTimeField, Case, When
from django.db.models.functions import TruncMonth
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.conf import settings
from django.utils import timezone
from django.utils.dateformat import DateFormat
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from ..models import Thesis, Category, Submission, DownloadLog, RejectedThesis, Course, Department
from authapp.models import Profile

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
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role in [Profile.ADMIN, Profile.LIBRARIAN])
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

    months = []
    approved_data, pending_data, rejected_data = [], [], []

    for entry in sorted({item['month'] for item in monthly_trends if item['month']}):
        months.append(DateFormat(entry).format('M'))
        month_entries = [e for e in monthly_trends if e['month'] == entry]
        approved_data.append(next((e['count'] for e in month_entries if e['status'] == 'approved'), 0))
        pending_data.append(next((e['count'] for e in month_entries if e['status'] == 'pending'), 0))
        rejected_data.append(next((e['count'] for e in month_entries if e['status'] == 'rejected'), 0))

    theses_by_course = list(
        Submission.objects
        .filter(status='approved', approved_at__isnull=False, course__isnull=False)
        .values(course_name=F('course__name'))
        .annotate(count=Count('id'))
        .order_by('-count')[:16]
    )
    for item in theses_by_course:
        name = item['course_name']
        item['course_name'] = " ".join(name.split()[4:]) if len(name.split()) > 4 else name

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
    archived_theses_count = len([f for f in os.listdir(archive_path) if os.path.isfile(os.path.join(archive_path, f))]) if os.path.exists(archive_path) else 0

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

def _refine_log_data(log):
    """Helper to translate technical log entries into human-readable text."""
    action_map = {1: "Created", 2: "Updated", 3: "Removed"}
    action = action_map.get(log.action_flag, "System Task")
    details = log.change_message
    
    msg = log.change_message
    model_name = log.content_type.model.lower()
    
    if "[APPROVED]" in msg:
        action = "Thesis Approved"
        details = msg.replace("[APPROVED]", "").strip()
    elif "[REJECTED]" in msg:
        action = "Thesis Rejected"
        details = msg.replace("[REJECTED]", "").strip()
    elif "Archived thesis" in msg:
        action = "System Archival"
        details = "Thesis record archived due to age (10+ years)."
    elif "Permanently deleted user" in msg:
        action = "Account Deletion"
    elif "Updated user role" in msg:
        action = "Role Assignment"
    elif "BULK IMPORT" in msg:
        action = "Data Import"
    elif "Login" in msg or "password" in msg:
        action = "Security Alert"
    elif not msg:
        if log.action_flag == 1: action = f"New {model_name.capitalize()}"
        elif log.action_flag == 2: action = f"Edit {model_name.capitalize()}"
        elif log.action_flag == 3: action = f"Delete {model_name.capitalize()}"
        details = f"Administrative action on {model_name} record."

    return action, details

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def admin_log_entries(request):
    all_logs_qs = LogEntry.objects.all().select_related('user', 'content_type').order_by('-action_time')
    
    # Process logs for display
    def process_logs(qs):
        processed = []
        for log in qs:
            action, details = _refine_log_data(log)
            log.refined_action = action
            log.refined_details = details
            processed.append(log)
        return processed

    security_logs = process_logs(all_logs_qs.filter(Q(change_message__icontains='Login') | Q(change_message__icontains='password') | Q(change_message__icontains='reset')))
    user_logs     = process_logs(all_logs_qs.filter(Q(change_message__icontains='role') | Q(change_message__icontains='deleted user')))
    thesis_logs   = process_logs(all_logs_qs.filter(Q(change_message__icontains='APPROVED') | Q(change_message__icontains='Rejected') | Q(change_message__icontains='Submission') | Q(change_message__icontains='Thesis')))
    import_logs   = process_logs(all_logs_qs.filter(change_message__icontains='BULK IMPORT'))
    all_logs      = process_logs(all_logs_qs)

    active_tab = request.GET.get('tab', 'all')
    return render(request, 'main/admin_log_entries.html', {
        'all_logs': all_logs, 'security_logs': security_logs, 'user_logs': user_logs,
        'thesis_logs': thesis_logs, 'import_logs': import_logs, 'active_tab': active_tab
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def password_reset_requests(request):
    """View active password reset codes and activation codes for offline assistance."""
    from ..models import PasswordResetCode, VerificationCode
    active_resets = PasswordResetCode.objects.filter(is_used=False, expires_at__gt=timezone.now()).select_related('user').order_by('-created_at')
    active_activations = VerificationCode.objects.filter(is_verified=False, expires_at__gt=timezone.now()).select_related('user').order_by('-created_at')
    
    return render(request, 'main/admin_reset_codes.html', {
        'active_codes': active_resets,
        'active_activations': active_activations
    })

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def user_list(request):
    all_users = User.objects.select_related('profile').order_by('-date_joined')
    admins     = all_users.filter(profile__role=Profile.ADMIN)
    librarians = all_users.filter(profile__role=Profile.LIBRARIAN)
    professors = all_users.filter(profile__role=Profile.PROFESSOR)
    students   = all_users.filter(profile__role=Profile.STUDENT)
    active_tab = request.GET.get('tab', 'admin')
    return render(request, 'main/user_list.html', {
        'admins': admins, 'librarians': librarians, 'professors': professors,
        'students': students, 'active_tab': active_tab, 'total_count': all_users.count(),
    })

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    username = user.username
    user.delete()
    log_admin_action(request.user, request.user, DELETION, f"Permanently deleted user account: {username}")
    return redirect('user_list')

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def edit_user(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        role = request.POST.get('role')
        profile, _ = Profile.objects.get_or_create(user=target_user)
        if role:
            profile.role = role
            profile.save()
            target_user.is_staff = (role in [Profile.ADMIN, Profile.LIBRARIAN])
            target_user.save()
            log_admin_action(request.user, target_user, CHANGE, f"Updated user role to: {role}")
        messages.success(request, "User role updated successfully.")
        return redirect('user_list')
    return render(request, 'main/edit_user.html', {'edit_user': target_user})

@login_required
@user_passes_test(lambda u: u.is_staff)
def pending_submissions(request):
    theses = Submission.objects.filter(status='pending').order_by('-created_at')
    return render(request, 'main/pending_submissions.html', {'theses': theses})

@login_required
@user_passes_test(lambda u: u.is_staff)
def approve_thesis(request, thesis_id):
    submission = get_object_or_404(Submission, id=thesis_id)
    if submission.status == Submission.STATUS_APPROVED:
        messages.info(request, f"Submission '{submission.title}' is already approved.")
        return redirect('pending_submissions')
    if request.method == 'POST':
        lc_classification = request.POST.get('lc_classification', '').strip()
        try:
            thesis = submission.approve(approved_by=request.user, lc_classification=lc_classification)
            # Cleanup auto logs
            LogEntry.objects.filter(user=request.user, content_type=ContentType.objects.get_for_model(thesis), object_id=thesis.id, action_flag=ADDITION).delete()
            LogEntry.objects.filter(user=request.user, content_type=ContentType.objects.get_for_model(submission), object_id=submission.id, action_flag__in=[CHANGE, DELETION]).delete()
            log_admin_action(request.user, thesis, ADDITION, f"[APPROVED] Submission '{submission.title}' and moved to Thesis table")
            messages.success(request, f"Submission '{submission.title}' approved successfully.")
        except ValueError as e:
            messages.error(request, f"Could not approve '{submission.title}': {str(e)}")
    return redirect('pending_submissions')

@login_required
@user_passes_test(lambda u: u.is_staff)
def reject_thesis(request, thesis_id):
    submission = get_object_or_404(Submission, id=thesis_id)
    if request.method == 'POST':
        if submission.status == Submission.STATUS_REJECTED: return redirect('pending_submissions')
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        if not rejection_reason:
            messages.error(request, "Rejection reason is required.")
            return redirect('pending_submissions')
        try:
            rejected_thesis = submission.reject(rejection_reason=rejection_reason, rejected_by=request.user)
            # Cleanup
            LogEntry.objects.filter(user=request.user, content_type=ContentType.objects.get_for_model(rejected_thesis), object_id=rejected_thesis.id, action_flag=ADDITION).delete()
            LogEntry.objects.filter(user=request.user, content_type=ContentType.objects.get_for_model(submission), object_id=submission.id, action_flag__in=[CHANGE, DELETION]).delete()
            log_admin_action(request.user, rejected_thesis, ADDITION, f"[REJECTED] Submission '{submission.title}' - Reason: {rejection_reason[:100]}")
            messages.success(request, f"Successfully rejected '{submission.title}'.")
        except ValueError as e:
            messages.error(request, f"Could not reject: {str(e)}")
        return redirect('pending_submissions')
    return render(request, 'main/reject_thesis.html', {'submission': submission})

@login_required
@user_passes_test(lambda u: u.is_staff)
def theses_list(request):
    theses = Thesis.objects.filter(is_archived=False)
    for thesis in theses:
        thesis.course_display = str(thesis.course).split('-')[0].strip() if thesis.course else "N/A"
    return render(request, 'main/theses.html', {'theses': theses})

@login_required
@user_passes_test(lambda u: u.is_staff)
def rejected_thesis_list(request):
    rejected_theses = RejectedThesis.objects.all()
    for thesis in rejected_theses:
        thesis.course_display = str(thesis.course).split('-')[0].strip() if thesis.course else "N/A"
    return render(request, 'main/rejected_thesis.html', {'rejected_theses': rejected_theses})

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

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_categories(request):
    categories = Category.objects.all()
    category_data = []
    for category in categories:
        category_data.append({
            'name': category.name,
            'department_count': category.departments.count(),
            'course_count': sum(dept.courses.count() for dept in category.departments.all()),
        })
    return render(request, 'main/admin_categories.html', {'categories': category_data})

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def archive_old_theses(request):
    if request.method != "POST": return JsonResponse({"error": "Invalid"}, status=400)
    system_user = User.objects.filter(is_superuser=True).first()
    cutoff_year = datetime.now().year - 10
    old_theses = Thesis.objects.filter(year__lte=cutoff_year)
    archived_count = 0
    for thesis in old_theses:
        # We no longer delete co-authors or the record itself to preserve metadata like LC Classification
        # Submission.objects.filter(title=thesis.title, author=thesis.author, year=thesis.year, status=Submission.STATUS_APPROVED).delete()
        
        if thesis.file and thesis.file.name:
            old_path = thesis.file.path
            archive_dir = os.path.join(settings.MEDIA_ROOT, "thesis_files", "Archived")
            os.makedirs(archive_dir, exist_ok=True)
            filename = os.path.basename(old_path)
            new_path = os.path.join(archive_dir, filename)
            if os.path.exists(old_path):
                shutil.move(old_path, new_path)
                thesis.file.name = f"thesis_files/Archived/{filename}"
        
        thesis.is_archived = True
        thesis.save()
        archived_count += 1
        log_admin_action(system_user, thesis, CHANGE, "Archived thesis (Metadata preserved)")
    return JsonResponse({"archived": archived_count})
@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def export_system_logs(request):
    """
    Professional Excel export for System Audit Logs.
    Supports period filtering (day, week, month, year, all) 
    and tab filtering (security, user, thesis, import, all).
    """
    period = request.GET.get('period', 'all')
    tab = request.GET.get('tab', 'all')
    
    all_logs = LogEntry.objects.select_related('user', 'content_type', 'user__profile').order_by('-action_time')
    
    # 1. Period Filtering
    now = timezone.now()
    if period == 'day':
        all_logs = all_logs.filter(action_time__gte=now - timezone.timedelta(days=1))
    elif period == 'week':
        all_logs = all_logs.filter(action_time__gte=now - timezone.timedelta(weeks=1))
    elif period == 'month':
        all_logs = all_logs.filter(action_time__gte=now - timezone.timedelta(days=30))
    elif period == 'year':
        all_logs = all_logs.filter(action_time__gte=now - timezone.timedelta(days=365))

    # 2. Tab Filtering
    if tab == 'security':
        all_logs = all_logs.filter(Q(change_message__icontains='Login') | Q(change_message__icontains='password') | Q(change_message__icontains='reset'))
    elif tab == 'user':
        all_logs = all_logs.filter(Q(change_message__icontains='role') | Q(change_message__icontains='deleted user'))
    elif tab == 'thesis':
        all_logs = all_logs.filter(Q(change_message__icontains='APPROVED') | Q(change_message__icontains='Rejected') | Q(change_message__icontains='Submission') | Q(change_message__icontains='Thesis'))
    elif tab == 'import':
        all_logs = all_logs.filter(change_message__icontains='BULK IMPORT')

    # Create Workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "System Audit Logs"

    # Define Styles
    header_fill = PatternFill(start_color="1B5E20", end_color="1B5E20", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    sub_header_fill = PatternFill(start_color="E8F5E9", end_color="E8F5E9", fill_type="solid")
    border = Border(
        left=Side(style='thin', color="DDDDDD"),
        right=Side(style='thin', color="DDDDDD"),
        top=Side(style='thin', color="DDDDDD"),
        bottom=Side(style='thin', color="DDDDDD")
    )
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center", wrap_text=True)

    # Title & Metadata
    ws.merge_cells('A1:G1')
    ws['A1'] = "THESIS LIBRARY SYSTEM - AUDIT LOG REPORT"
    ws['A1'].font = Font(bold=True, size=16, color="1B5E20")
    ws['A1'].alignment = center_align
    
    ws.merge_cells('A2:G2')
    ws['A2'] = f"Report Period: {period.upper()} | Generated on: {now.strftime('%B %d, %Y %I:%M %p')}"
    ws['A2'].font = Font(italic=True, size=10)
    ws['A2'].alignment = center_align
    
    ws.append([]) # Empty row

    # Table Headers
    headers = ["Timestamp", "User", "Role", "System Module", "Specific Item", "Action Taken", "Details"]
    ws.append(headers)
    
    header_row = 4
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = border

    for idx, log in enumerate(all_logs, 1):
        row_num = header_row + idx
        role = log.user.profile.get_role_display() if hasattr(log.user, 'profile') else "N/A"
        
        # Use refinement helper
        action, details = _refine_log_data(log)
        
        row_data = [
            log.action_time.strftime("%Y-%m-%d %I:%M %p"),
            log.user.username,
            role,
            log.content_type.model.capitalize(),
            log.object_repr,
            action.upper(),
            details
        ]
        
        for col_num, value in enumerate(row_data, 1):
            cell = ws.cell(row=row_num, column=col_num)
            cell.value = value
            cell.border = border
            cell.alignment = left_align if col_num in [5, 7] else center_align
            
            # Alternate row colors
            if idx % 2 == 0:
                cell.fill = PatternFill(start_color="F9F9F9", end_color="F9F9F9", fill_type="solid")

    # Set column widths
    dims = {
        'A': 22, # Timestamp
        'B': 15, # User
        'C': 12, # Role
        'D': 15, # Module
        'E': 30, # Item
        'F': 15, # Action
        'G': 50  # Details
    }
    for col, value in dims.items():
        ws.column_dimensions[col].width = value

    # Freeze top rows
    ws.freeze_panes = "A5"

    # Prepare Response
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"System_Log_{tab.upper()}_{period.upper()}_{now.strftime('%Y%m%d')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    
    return response
