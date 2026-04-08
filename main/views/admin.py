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
from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings
from django.utils import timezone
from django.utils.dateformat import DateFormat

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

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def admin_log_entries(request):
    all_logs = LogEntry.objects.all().select_related('user', 'content_type').order_by('-action_time')
    security_logs = all_logs.filter(Q(change_message__icontains='Login') | Q(change_message__icontains='password') | Q(change_message__icontains='reset'))
    user_logs     = all_logs.filter(Q(change_message__icontains='role') | Q(change_message__icontains='deleted user'))
    thesis_logs   = all_logs.filter(Q(change_message__icontains='APPROVED') | Q(change_message__icontains='Rejected') | Q(change_message__icontains='Submission') | Q(change_message__icontains='Thesis'))
    import_logs   = all_logs.filter(change_message__icontains='BULK IMPORT')
    active_tab = request.GET.get('tab', 'all')
    return render(request, 'main/admin_log_entries.html', {
        'all_logs': all_logs, 'security_logs': security_logs, 'user_logs': user_logs,
        'thesis_logs': thesis_logs, 'import_logs': import_logs, 'active_tab': active_tab
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
    theses = Thesis.objects.all()
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
        thesis.co_authors.all().delete()
        Submission.objects.filter(title=thesis.title, author=thesis.author, year=thesis.year, status=Submission.STATUS_APPROVED).delete()
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
        log_admin_action(system_user, thesis, DELETION, "Archived thesis older than 10 years")
        thesis.delete()
    return JsonResponse({"archived": archived_count})
