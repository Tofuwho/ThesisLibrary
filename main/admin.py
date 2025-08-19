from django.contrib import admin
from django.utils.html import format_html
from .models import Thesis, Submission

@admin.register(Thesis)
class ThesisAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'year', 'thesis_type', 'specialization')
    # Add 'file' to fields if you use fieldsets or fields


@admin.action(description='Approve selected submissions')
def approve_submissions(modeladmin, request, queryset):
    for submission in queryset.filter(status=Submission.STATUS_SUBMITTED):
        submission.approve()


@admin.action(description='Reject selected submissions')
def reject_submissions(modeladmin, request, queryset):
    for submission in queryset.filter(status=Submission.STATUS_SUBMITTED):
        submission.reject()


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'submitter', 'status', 'created_at', 'approved_at', 'category', 'file_link'
    )
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('title', 'submitter__username', 'submitter__first_name', 'submitter__last_name')
    actions = [approve_submissions, reject_submissions]

    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">View</a>', obj.file.url)
        return '-'
    file_link.short_description = 'File'