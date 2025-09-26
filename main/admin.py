from django.contrib import admin
from django.contrib.admin import AdminSite
from django import forms
from django.utils.html import format_html
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import path
from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from django.contrib.admin.models import LogEntry, CHANGE, DELETION, ADDITION
from django.contrib.contenttypes.models import ContentType
from .models import Thesis, SubmissionCoAuthor, CoAuthor, Submission, Category, Department, Course, RejectedThesis, DownloadLog
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

class CoAuthorInline(admin.TabularInline):
    model = CoAuthor
    extra = 1
    fields = ('first_name', 'last_name', 'student_id', 'email')
    ordering = ('first_name', 'last_name')


class SubmissionCoAuthorInline(admin.TabularInline):
    model = SubmissionCoAuthor
    extra = 1
    fields = ('first_name', 'last_name', 'student_id', 'email')
    ordering = ('first_name', 'last_name')


def log_admin_action(user, obj, action_flag, message):
    """Helper function to log admin actions to Recent Actions."""
    try:
        content_type = ContentType.objects.get_for_model(obj)
        LogEntry.objects.log_action(
            user_id=user.pk,
            content_type_id=content_type.pk,
            object_id=obj.pk,
            object_repr=str(obj),
            action_flag=action_flag,
            change_message=message,
        )
    except Exception as e:
        pass



@admin.register(Thesis)
class ThesisAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "year", "department", "course", "thesis_type", "co_authors_count")
    inlines = [CoAuthorInline]
    list_filter = ("department", "course", "year", "thesis_type")
    search_fields = ("title", "author", "abstract")
    ordering = ("-year", "title")
    autocomplete_fields = ("category", "department", "course")

    fieldsets = (
        ("Thesis Information", {
            "fields": ("title", "author", "year", "abstract"),
        }),
        ("Extended Metadata", {
            "fields": ("keywords", "research_category", "expected_completion"),
        }),
        ("Classification", {
            "fields": ("category", "department", "course"),
        }),
        ("Additional Details", {
            "fields": ("thesis_type", "specialization"),
        }),
        ("Supervisor Information", {
            "fields": (
                "supervisor_name", "supervisor_email", "supervisor_department", "supervisor_title",
                "co_supervisor_name", "co_supervisor_email",
            ),
        }),
        ("Files", {
            "fields": ("file",),
        }),
    )

    def co_authors_count(self, obj):
        """Display the number of co-authors for this thesis."""
        if obj:
            count = obj.co_authors.count()
            return f"{count} co-author{'s' if count != 1 else ''}"
        return "0 co-authors"
    co_authors_count.short_description = "Co-Authors"
    
    def save_model(self, request, obj, form, change):
        """Override save to log actions."""
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """Custom delete method with confirmation."""
        messages.warning(request, f'You are about to permanently delete the thesis: "{obj.title}". This action cannot be undone.')
        
        return super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        """Custom bulk delete method with confirmation."""
        thesis_titles = [f'"{thesis.title}"' for thesis in queryset]
        messages.warning(request, f'You are about to permanently delete {len(queryset)} thesis(es): {", ".join(thesis_titles)}. This action cannot be undone.')
        
        return super().delete_queryset(request, queryset)


# --- Admin Actions ---
@admin.action(description="Approve selected pending submissions")
def approve_submissions(modeladmin, request, queryset):
    from django.contrib.admin.models import LogEntry
    from django.contrib.contenttypes.models import ContentType
    
    pending_submissions = queryset.filter(status=Submission.STATUS_PENDING)
    approved_count = 0
    
    for submission in pending_submissions:
        try:
            # Store submission title before approval
            submission_title = submission.title
            
            # Approve the submission
            thesis = submission.approve(approved_by=request.user)
            approved_count += 1
            
            # Remove the automatic Thesis creation log entry
            thesis_ct = ContentType.objects.get_for_model(thesis)
            LogEntry.objects.filter(
                user=request.user,
                content_type=thesis_ct,
                object_id=thesis.id,
                action_flag=ADDITION
            ).delete()
            # Remove all automatic logs for the Submission (EDITED, DELETED)
            submission_ct = ContentType.objects.get_for_model(submission)
            LogEntry.objects.filter(
                user=request.user,
                content_type=submission_ct,
                object_id=submission.id,
                action_flag__in=[CHANGE, DELETION]
            ).delete()
            
            # Log only our custom approval action
            log_admin_action(
                request.user, 
                thesis, 
                ADDITION, 
                f"[APPROVED] Submission '{submission_title}' and moved to Thesis table"
            )
            
        except ValueError as e:
            messages.error(request, f"Could not approve '{submission.title}': {str(e)}")
    
    if approved_count > 0:
        messages.success(request, f"Successfully approved {approved_count} submission(s). They have been moved to the Thesis table.")


@admin.action(description="Reject selected pending submissions")
def reject_submissions(modeladmin, request, queryset):
    from django.contrib.admin.models import LogEntry
    from django.contrib.contenttypes.models import ContentType
    
    pending_submissions = queryset.filter(status=Submission.STATUS_PENDING)
    rejected_count = 0
    
    for submission in pending_submissions:
        try:
            # Store submission title before rejection
            submission_title = submission.title
            
            # Reject the submission
            rejected_thesis = submission.reject(rejection_reason="Rejected via admin action", rejected_by=request.user)
            rejected_count += 1
            
            # Remove the automatic RejectedThesis creation log entry
            rejected_ct = ContentType.objects.get_for_model(rejected_thesis)
            LogEntry.objects.filter(
                user=request.user,
                content_type=rejected_ct,
                object_id=rejected_thesis.id,
                action_flag=ADDITION
            ).delete()
            # Remove all automatic logs for the Submission (EDITED, DELETED)
            submission_ct = ContentType.objects.get_for_model(submission)
            LogEntry.objects.filter(
                user=request.user,
                content_type=submission_ct,
                object_id=submission.id,
                action_flag__in=[CHANGE, DELETION]
            ).delete()
            
            # Log only our custom rejection action
            log_admin_action(
                request.user, 
                rejected_thesis, 
                ADDITION, 
                f"[REJECTED] Submission '{submission_title}' and moved to Rejected Thesis archive"
            )
            
        except ValueError as e:
            messages.error(request, f"Could not reject '{submission.title}': {str(e)}")
    
    if rejected_count > 0:
        messages.success(request, f"Successfully rejected {rejected_count} submission(s). They have been moved to the Rejected Thesis archive.")



@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    """
    Admin for managing Submissions with relational CoAuthors.
    """
    list_display = ("title", "submitter", "category", "department", "course", "status", "created_at", "co_authors_count")
    search_fields = ("title", "submitter__username", "submitter__first_name", "submitter__last_name")
    list_filter = ("status", "category", "department", "course", "created_at")
    actions = [approve_submissions, reject_submissions]

    inlines = [SubmissionCoAuthorInline]

    readonly_fields = ("created_at", "updated_at", "status", "file_link", "approval_sheet_preview", "submitter_username", "submitter_email")
    autocomplete_fields = ("category", "department", "course")

    fieldsets = (
        ("Submission Information", {
            "fields": ("title", "author", "year", "abstract", "keywords", "research_category", "expected_completion"),
        }),
        ("Classification", {
            "fields": ("category", "department", "course"),
        }),
        ("Additional Details", {
            "fields": ("thesis_type", "specialization"),
        }),
        ("Supervisor Information", {
            "fields": (
                "supervisor_name", "supervisor_email", "supervisor_department", "supervisor_title",
                "co_supervisor_name", "co_supervisor_email",
            ),
        }),
        ("Files", {
            "fields": ("file", "approval_sheet", "file_link", "approval_sheet_preview"),
        }),
        ("Review & Timestamps", {
            "fields": ("review_state", "decision_note", "status", "created_at", "updated_at"),
        }),
        ("Submitter", {
            "fields": ("submitter", "submitter_username", "submitter_email"),
        }),
    )

    def get_queryset(self, request):
        """Show only pending submissions in this admin list.

        Approved or rejected submissions remain in the database for
        student history, but they won't appear in the pending list.
        """
        queryset = super().get_queryset(request)
        return queryset.filter(status=Submission.STATUS_PENDING)

    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">View</a>', obj.file.url)
        return "-"
    file_link.short_description = "File"

    def approval_sheet_preview(self, obj):
        if obj.approval_sheet:
            return format_html(
                '<img src="{}" width="80" height="80" style="object-fit:cover; border-radius:6px;" />',
                obj.approval_sheet.url,
            )
        return "-"
    approval_sheet_preview.short_description = "Approval Sheet"

    def submitter_username(self, obj):
        return obj.submitter.username if obj and obj.submitter else "-"
    submitter_username.short_description = "Submitter Username"

    def submitter_email(self, obj):
        return obj.submitter.email if obj and obj.submitter else "-"
    submitter_email.short_description = "Submitter Email"
    
    def co_authors_count(self, obj):
        """Display the number of co-authors for this submission."""
        if obj:
            count = obj.co_authors.count()
            return f"{count} co-author{'s' if count != 1 else ''}"
        return "0 co-authors"
    co_authors_count.short_description = "Co-Authors"


@admin.register(RejectedThesis)
class RejectedThesisAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "original_submitter",
        "category",
        "department",
        "course",
        "rejected_at",
        "rejected_by",
        "rejection_reason_preview",
        "file_link",
    )
    list_filter = (
        "category",
        "department",
        "course",
        "rejected_at",
        "rejected_by",
    )
    search_fields = (
        "title",
        "author",
        "original_submitter__username",
        "original_submitter__first_name",
        "original_submitter__last_name",
        "rejection_reason",
    )
    readonly_fields = ("rejected_at", "original_submission_id")
    ordering = ("-rejected_at",)
    
    def save_model(self, request, obj, form, change):
        """Override save to log actions."""
        super().save_model(request, obj, form, change)
    
    def rejection_reason_preview(self, obj):
        """Show truncated rejection reason."""
        if obj.rejection_reason:
            return obj.rejection_reason[:50] + "..." if len(obj.rejection_reason) > 50 else obj.rejection_reason
        return "-"
    rejection_reason_preview.short_description = "Rejection Reason"
    
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">View</a>', obj.file.url)
        return "-"
    file_link.short_description = "File"
    
    def delete_model(self, request, obj):
        """Custom delete method with confirmation."""
        messages.warning(request, f'You are about to permanently delete the rejected thesis: "{obj.title}". This action cannot be undone.')
        
        return super().delete_model(request, obj)
    
    def delete_queryset(self, request, queryset):
        """Custom bulk delete method with confirmation."""
        thesis_titles = [f'"{thesis.title}"' for thesis in queryset]
        messages.warning(request, f'You are about to permanently delete {len(queryset)} rejected thesis(es): {", ".join(thesis_titles)}. This action cannot be undone.')
        
        return super().delete_queryset(request, queryset)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for research categories with department and course counts."""
    list_display = ("name", "department_count", "course_count")
    search_fields = ("name",)

    def save_model(self, request, obj, form, change):
        """Override save to log actions."""
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        """Override delete to log actions."""
        return super().delete_model(request, obj)

    def department_count(self, obj):
        return obj.departments.count()
    department_count.short_description = "Departments"

    def course_count(self, obj):
        total = sum(dept.courses.count() for dept in obj.departments.all())
        return total
    course_count.short_description = "Total Courses"


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Admin for academic departments with course counts."""
    list_display = ("name", "category", "course_count")
    list_filter = ("category",)
    search_fields = ("name",)
    ordering = ("category__name", "name")

    def save_model(self, request, obj, form, change):
        """Override save to log actions."""
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        """Override delete to log actions."""
        return super().delete_model(request, obj)

    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = "Courses"


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Admin for academic courses showing full path (Category → Department)."""
    list_display = ("name", "department", "category", "full_path")
    list_filter = ("department__category", "department")
    search_fields = ("name", "department__name")
    ordering = ("department__category__name", "department__name", "name")

    def save_model(self, request, obj, form, change):
        """Override save to log actions."""
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        """Override delete to log actions."""
        return super().delete_model(request, obj)

    def category(self, obj):
        return obj.department.category.name if obj.department else "-"
    category.short_description = "Category"

    def full_path(self, obj):
        if obj.department and obj.department.category:
            return f"{obj.department.category.name} → {obj.department.name}"
        return "-"
    full_path.short_description = "Academic Path"

@admin.register(DownloadLog)
class DownloadLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'thesis_title_short', 'ip_address')
    list_filter = ('timestamp', 'user')
    search_fields = ('user__username', 'thesis__title', 'ip_address')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    
    readonly_fields = ('user', 'thesis', 'timestamp', 'ip_address', 'user_agent')
    
    def thesis_title_short(self, obj):
        title = obj.thesis.title
        return title[:50] + '...' if len(title) > 50 else title
    thesis_title_short.short_description = 'Thesis Title'
    thesis_title_short.admin_order_field = 'thesis__title'
    
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag', 'change_message')
    list_filter = ('user', 'content_type', 'action_flag')
    search_fields = ('object_repr', 'change_message')
    date_hierarchy = 'action_time'

# Custom admin site with system logs functionality
class CustomAdminSite(admin.AdminSite):
    """
    Custom admin site configuration:
    - Custom header and title
    - Adds a 'System Logs' page to view recent activity
    """
    site_header = "Thesis Library Admin"
    site_title = "Thesis Library Admin Portal"
    index_title = "Welcome to the Thesis Library Administration"

    def get_urls(self):
        """Add custom URLs on top of default admin URLs."""
        urls = super().get_urls()
        custom_urls = [
            path("system-logs/", self.admin_view(self.system_logs_view), name="system_logs"),
        ]
        return custom_urls + urls

    def system_logs_view(self, request):
        """
        Custom view for displaying the 50 most recent system logs.
        Uses Django's LogEntry model.
        """
        logs = LogEntry.objects.select_related("content_type", "user").order_by("-action_time")[:50]
        context = dict(
            self.each_context(request),
            title="System Logs",
            logs=logs,
        )
        return TemplateResponse(request, "admin/system_logs.html", context)

# Create the custom admin site
custom_admin_site = CustomAdminSite(name='custom_admin')

# Register all your models with the custom admin site
custom_admin_site.register(Thesis, ThesisAdmin)
custom_admin_site.register(Submission, SubmissionAdmin)
custom_admin_site.register(RejectedThesis, RejectedThesisAdmin)
custom_admin_site.register(Category, CategoryAdmin)
custom_admin_site.register(Department, DepartmentAdmin)
custom_admin_site.register(Course, CourseAdmin)
custom_admin_site.register(LogEntry, LogEntryAdmin)
custom_admin_site.register(DownloadLog, DownloadLogAdmin)
custom_admin_site.register(User, UserAdmin)
custom_admin_site.register(Group, GroupAdmin)