# ruff: noqa: F403, F405, E402
from django.contrib.admin import AdminSite
from django.contrib.admin.models import LogEntry
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group
from .admin import *

class CustomAdminSite(AdminSite):
    site_header = 'Thesis Library Administration'
    site_title = 'Thesis Library Admin'
    index_title = 'Thesis Library Administration'
    index_template = 'admin/index.html'
    
    def index(self, request, extra_context=None):
        """
        Display the main admin index page with enhanced recent actions.
        """
        extra_context = extra_context or {}
        
        # Get recent actions
        recent_actions = LogEntry.objects.filter(
            user=request.user
        ).select_related('content_type', 'user')[:10]
        
        extra_context.update({
            'recent_actions': recent_actions,
        })
        
        return super().index(request, extra_context)

# Create custom admin site instance
admin_site = CustomAdminSite(name='custom_admin')

# Register all models with the custom admin site
from .models import Thesis, Submission, Category, Department, Course, RejectedThesis

# Register User and Group with custom admin site
admin_site.register(User, UserAdmin)
admin_site.register(Group)

# Register with custom admin site
admin_site.register(Thesis, ThesisAdmin)
admin_site.register(Submission, SubmissionAdmin)
admin_site.register(Category, CategoryAdmin)
admin_site.register(Department, DepartmentAdmin)
admin_site.register(Course, CourseAdmin)
admin_site.register(RejectedThesis, RejectedThesisAdmin)
