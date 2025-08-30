from django.contrib import admin
from django.utils.html import format_html
from .models import Thesis, Submission, Category, Department, Course


@admin.register(Thesis)
class ThesisAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "year", "thesis_type", "specialization")


# --- Admin Actions ---
@admin.action(description="Approve selected submissions")
def approve_submissions(modeladmin, request, queryset):
    for submission in queryset.filter(status=Submission.STATUS_SUBMITTED):
        submission.approve()


@admin.action(description="Reject selected submissions")
def reject_submissions(modeladmin, request, queryset):
    for submission in queryset.filter(status=Submission.STATUS_SUBMITTED):
        submission.reject()


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "submitter",
        "category",
        "department",
        "course",
        "status",
        "created_at",
        "approved_at",
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


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "department_count", "course_count")
    search_fields = ("name",)
    
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
    
    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = "Courses"


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "category", "full_path")
    list_filter = ("department__category", "department")
    search_fields = ("name", "department__name")
    ordering = ("department__category__name", "department__name", "name")
    
    def category(self, obj):
        return obj.department.category.name if obj.department else "-"
    category.short_description = "Category"
    
    def full_path(self, obj):
        if obj.department and obj.department.category:
            return f"{obj.department.category.name} → {obj.department.name}"
        return "-"
    full_path.short_description = "Academic Path"
