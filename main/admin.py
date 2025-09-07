from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path
from django.http import HttpResponseRedirect
from django.contrib.admin.models import LogEntry, CHANGE, DELETION, ADDITION
from django.contrib.contenttypes.models import ContentType
from .models import Thesis, Submission, Category, Department, Course, RejectedThesis
from django.contrib.admin.models import LogEntry


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
        # If logging fails, don't break the main action
        pass


class ThesisAdminForm(forms.ModelForm):
    # Separate inputs for up to 3 co-authors
    co_author1_name = forms.CharField(required=False, label="Co-Author 1 Name")
    co_author1_id = forms.CharField(required=False, label="Co-Author 1 Student ID")
    co_author1_email = forms.EmailField(required=False, label="Co-Author 1 Email")
    co_author2_name = forms.CharField(required=False, label="Co-Author 2 Name")
    co_author2_id = forms.CharField(required=False, label="Co-Author 2 Student ID")
    co_author2_email = forms.EmailField(required=False, label="Co-Author 2 Email")
    co_author3_name = forms.CharField(required=False, label="Co-Author 3 Name")
    co_author3_id = forms.CharField(required=False, label="Co-Author 3 Student ID")
    co_author3_email = forms.EmailField(required=False, label="Co-Author 3 Email")

    class Meta:
        from .models import Thesis
        model = Thesis
        fields = "__all__"
        widgets = {
            'co_authors': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        if instance and isinstance(instance.co_authors, list):
            try:
                for idx, item in enumerate(instance.co_authors[:3], start=1):
                    if isinstance(item, dict):
                        first = (item.get('first_name') or '').strip()
                        last = (item.get('last_name') or '').strip()
                        full = (first + ' ' + last).strip() or (item.get('name') or '').strip()
                        sid = (item.get('student_id') or '').strip()
                        email = (item.get('email') or '').strip()
                        self.initial[f'co_author{idx}_name'] = full
                        self.initial[f'co_author{idx}_id'] = sid
                        self.initial[f'co_author{idx}_email'] = email
                    elif isinstance(item, str) and item.strip():
                        self.initial[f'co_author{idx}_name'] = item.strip()
            except Exception:
                pass

    def clean(self):
        cleaned = super().clean()
        coauthors = []
        for idx in range(1, 4):
            name = (cleaned.get(f'co_author{idx}_name') or '').strip()
            sid = (cleaned.get(f'co_author{idx}_id') or '').strip()
            email = (cleaned.get(f'co_author{idx}_email') or '').strip()
            if any([name, sid, email]):
                # Try to split name into first/last for consistency
                first, last = None, None
                if name:
                    parts = name.split()
                    if len(parts) == 1:
                        first = parts[0]
                    else:
                        first = ' '.join(parts[:-1])
                        last = parts[-1]
                entry = {
                    'first_name': first or '',
                    'last_name': last or '',
                    'student_id': sid,
                    'email': email,
                }
                coauthors.append(entry)
        cleaned['co_authors'] = coauthors
        return cleaned


@admin.register(Thesis)
class ThesisAdmin(admin.ModelAdmin):
    form = ThesisAdminForm
    list_display = ("title", "author", "year", "department", "course", "thesis_type")
    list_filter = ("department", "course", "year", "thesis_type")
    search_fields = ("title", "author", "co_author", "abstract")
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
        ("Co-Authors", {
            "fields": (
                "co_authors_display",
                "co_author1_name", "co_author1_id", "co_author1_email",
                "co_author2_name", "co_author2_id", "co_author2_email",
                "co_author3_name", "co_author3_id", "co_author3_email",
                "co_authors",
            ),
        }),
        ("Files", {
            "fields": ("file",),
        }),
    )

    readonly_fields = ("co_authors_display",)

    def co_authors_display(self, obj):
        if not obj or not obj.co_authors:
            return "-"
        items = []
        for item in obj.co_authors:
            if isinstance(item, dict):
                parts = []
                first = (item.get('first_name') or '').strip()
                last = (item.get('last_name') or '').strip()
                full = (first + ' ' + last).strip()
                if full:
                    parts.append(full)
                sid = (item.get('student_id') or '').strip()
                email = (item.get('email') or '').strip()
                meta = ", ".join([v for v in [sid if sid else None, email if email else None] if v])
                if meta:
                    parts.append(f"({meta})")
                label = " ".join(parts) if parts else None
                if label:
                    items.append(label)
            elif isinstance(item, str) and item.strip():
                items.append(item.strip())
        return "; ".join(items) if items else "-"
    co_authors_display.short_description = "Current Co-Authors"
    
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


class SubmissionAdminForm(forms.ModelForm):
    # Separate inputs for up to 3 co-authors
    co_author1_name = forms.CharField(required=False, label="Co-Author 1 Name")
    co_author1_id = forms.CharField(required=False, label="Co-Author 1 Student ID")
    co_author1_email = forms.EmailField(required=False, label="Co-Author 1 Email")
    co_author2_name = forms.CharField(required=False, label="Co-Author 2 Name")
    co_author2_id = forms.CharField(required=False, label="Co-Author 2 Student ID")
    co_author2_email = forms.EmailField(required=False, label="Co-Author 2 Email")
    co_author3_name = forms.CharField(required=False, label="Co-Author 3 Name")
    co_author3_id = forms.CharField(required=False, label="Co-Author 3 Student ID")
    co_author3_email = forms.EmailField(required=False, label="Co-Author 3 Email")

    class Meta:
        from .models import Submission
        model = Submission
        fields = "__all__"
        widgets = {
            'co_authors': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        if instance and isinstance(instance.co_authors, list):
            try:
                for idx, item in enumerate(instance.co_authors[:3], start=1):
                    if isinstance(item, dict):
                        first = (item.get('first_name') or '').strip()
                        last = (item.get('last_name') or '').strip()
                        full = (first + ' ' + last).strip() or (item.get('name') or '').strip()
                        sid = (item.get('student_id') or '').strip()
                        email = (item.get('email') or '').strip()
                        self.initial[f'co_author{idx}_name'] = full
                        self.initial[f'co_author{idx}_id'] = sid
                        self.initial[f'co_author{idx}_email'] = email
                    elif isinstance(item, str) and item.strip():
                        self.initial[f'co_author{idx}_name'] = item.strip()
            except Exception:
                pass

    def clean(self):
        cleaned = super().clean()
        coauthors = []
        for idx in range(1, 4):
            name = (cleaned.get(f'co_author{idx}_name') or '').strip()
            sid = (cleaned.get(f'co_author{idx}_id') or '').strip()
            email = (cleaned.get(f'co_author{idx}_email') or '').strip()
            if any([name, sid, email]):
                first, last = None, None
                if name:
                    parts = name.split()
                    if len(parts) == 1:
                        first = parts[0]
                    else:
                        first = ' '.join(parts[:-1])
                        last = parts[-1]
                entry = {
                    'first_name': first or '',
                    'last_name': last or '',
                    'student_id': sid,
                    'email': email,
                }
                coauthors.append(entry)
        cleaned['co_authors'] = coauthors
        return cleaned


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    form = SubmissionAdminForm
    list_display = (
        "title",
        "submitter",
        "category",
        "department",
        "course",
        "status",
        "created_at",
        "file_link",
        "approval_sheet_preview",
    )
    list_filter = (
        "status",
        "category",
        "department",
        "course",
        "created_at",
    )
    search_fields = (
        "title",
        "submitter__username",
        "submitter__first_name",
        "submitter__last_name",
    )
    actions = [approve_submissions, reject_submissions]
    readonly_fields = ("created_at", "updated_at", "status", "file_link", "approval_sheet_preview", "co_authors_display", "submitter_username", "submitter_email")
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
        ("Co-Authors", {
            "fields": (
                "co_authors_display",
                "co_author1_name", "co_author1_id", "co_author1_email",
                "co_author2_name", "co_author2_id", "co_author2_email",
                "co_author3_name", "co_author3_id", "co_author3_email",
                "co_authors",
            ),
        }),
        ("Files", {
            "fields": ("file", "approval_sheet", "file_link", "approval_sheet_preview"),
        }),
        ("Review & Timestamps", {
            "fields": ("review_state", "decision_note", "status", "created_at", "updated_at"),
            "description": "Set review intent. Actual approval/rejection happens via the actions above.",
        }),
        ("Submitter", {
            "fields": ("submitter", "submitter_username", "submitter_email"),
        }),
    )
    
    def get_queryset(self, request):
        """Only show pending submissions in the admin."""
        return super().get_queryset(request).filter(status=Submission.STATUS_PENDING)
    
    def save_model(self, request, obj, form, change):
        """Override save to log actions."""
        super().save_model(request, obj, form, change)

    # --- File link display ---
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">View</a>', obj.file.url)
        return "-"
    file_link.short_description = "File"

    # --- Approval sheet image preview ---
    def approval_sheet_preview(self, obj):
        if obj.approval_sheet:
            return format_html(
                '<img src="{}" width="80" height="80" style="object-fit:cover; border-radius:6px;" />',
                obj.approval_sheet.url,
            )
        return "-"
    approval_sheet_preview.short_description = "Approval Sheet"

    def co_authors_display(self, obj):
        if not obj or not obj.co_authors:
            return "-"
        items = []
        for item in obj.co_authors:
            if isinstance(item, dict):
                parts = []
                first = (item.get('first_name') or '').strip()
                last = (item.get('last_name') or '').strip()
                full = (first + ' ' + last).strip()
                if full:
                    parts.append(full)
                sid = (item.get('student_id') or '').strip()
                email = (item.get('email') or '').strip()
                meta = ", ".join([v for v in [sid if sid else None, email if email else None] if v])
                if meta:
                    parts.append(f"({meta})")
                label = " ".join(parts) if parts else None
                if label:
                    items.append(label)
            elif isinstance(item, str) and item.strip():
                items.append(item.strip())
        return "; ".join(items) if items else "-"
    co_authors_display.short_description = "Current Co-Authors"

    def submitter_username(self, obj):
        return obj.submitter.username if obj and obj.submitter else "-"
    submitter_username.short_description = "Submitter Username"

    def submitter_email(self, obj):
        return obj.submitter.email if obj and obj.submitter else "-"
    submitter_email.short_description = "Submitter Email"


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

@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_time', 'user', 'content_type', 'object_repr', 'action_flag', 'change_message')
    list_filter = ('user', 'content_type', 'action_flag')
    search_fields = ('object_repr', 'change_message')
    date_hierarchy = 'action_time'