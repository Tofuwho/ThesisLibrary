from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('about/', views.about_page, name='about'),
    path('views/', views.index_page, name='index'),
    path('categories/', views.categories_page, name='categories'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('category/<str:category_name>/', views.category_detail, name='category_detail'),
    path('student/submissions/create/', views.create_submission, name='create_submission'),
    path('student/submissions/mine/', views.my_submissions, name='my_submissions'),
    path('thesis/<int:pk>/', views.thesis_detail, name='thesis_detail'),
    path('thesis/<int:pk>/view/', views.view_thesis_file, name='thesis_view_file'),
    path('thesis/<int:pk>/view/highlight/', views.view_thesis_file_highlight, name='thesis_view_file_highlight'),
    path('thesis/<int:pk>/download/', views.download_thesis_file, name='thesis_download_file'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('verify-email/', views.verify_email_view, name='verify_email'),
    path('api/departments/<int:category_id>/', views.api_departments, name='api_departments'),
    path('api/courses/<int:department_id>/', views.api_courses, name='api_courses'),
    path('api/extract-abstract/', views.api_extract_abstract, name='api_extract_abstract'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-logs', views.admin_log_entries, name='admin_log_entries'),
    path('users/', views.user_list, name='user_list'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('users/change-password/<int:user_id>/', views.change_password, name='change_password'),
    path('pending-submissions/', views.pending_submissions, name='pending_submissions'),
    path('approve-thesis/<int:thesis_id>/', views.approve_thesis, name='approve_thesis'),
    path('view-thesis/<int:thesis_id>/', views.view_thesis, name='view_thesis'),
    path('reject-thesis/<int:thesis_id>/', views.reject_thesis, name='reject_thesis'),
    path('rejected-thesis/', views.rejected_thesis_list, name='rejected_thesis_list'),
    path('theses/', views.theses_list, name='theses_list'),
    path('departments/', views.departments_list, name='departments_list'),
    path('courses/', views.courses_list, name='courses_list'),
    path('students/', views.students_list, name='students_list'),
    path('professors/', views.professors_list, name='professors_list'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)