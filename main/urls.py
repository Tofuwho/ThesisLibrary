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
    path('profile/', views.profile_card, name='profile_card'),
    path('category/<str:category_name>/', views.category_detail, name='category_detail'),
    path('student/submissions/create/', views.create_submission, name='create_submission'),
    path('student/submissions/mine/', views.my_submissions, name='my_submissions'),
    path('thesis/<int:pk>/', views.thesis_detail, name='thesis_detail'),
    path('thesis/<int:pk>/download/', views.download_thesis_file, name='thesis_download_file'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('verify-email/', views.verify_email_view, name='verify_email'),
    path('activate-account/', views.activate_premade_account, name='activate_account'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('change-password/', views.change_password_profile, name='change_password_profile'),
    path('api/departments/<int:category_id>/', views.api_departments, name='api_departments'),
    path('api/courses/<int:department_id>/', views.api_courses, name='api_courses'),
    path('api/extract-abstract/', views.api_extract_abstract, name='api_extract_abstract'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-logs/', views.admin_log_entries, name='admin_log_entries'),
    path('admin-logs/export/', views.export_system_logs, name='export_system_logs'),
    path('management/reset-requests/', views.password_reset_requests, name='password_reset_requests'),
    path('users/', views.user_list, name='user_list'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('users/change-password/<int:user_id>/', views.change_password, name='change_password'),
    path('pending-submissions/', views.pending_submissions, name='pending_submissions'),
    path('approve-thesis/<int:thesis_id>/', views.approve_thesis, name='approve_thesis'),
    path('reject-thesis/<int:thesis_id>/', views.reject_thesis, name='reject_thesis'),
    path('rejected-thesis/', views.rejected_thesis_list, name='rejected_thesis_list'),
    path('theses/', views.theses_list, name='theses_list'),
    path('departments/', views.departments_list, name='departments_list'),
    path('courses/', views.courses_list, name='courses_list'),
    path('students/', views.students_list, name='students_list'),
    path('professors/', views.professors_list, name='professors_list'),
    path('import-students/', views.import_students, name='import_students'),
    path('add-student/', views.add_student, name='add_student'),
    path('edit-student/<str:student_id>/', views.edit_student, name='edit_student'),
    path('professor/add/', views.add_professor, name='add_professor'),
    path('professor/<str:professor_id>/edit/', views.edit_professor, name='edit_professor'),
    path('import-professors/', views.import_professors, name='import_professors'),
    path('admin-categories/', views.admin_categories, name='admin_categories'),
    path("archive-old-theses/", views.archive_old_theses, name="archive_old_theses"),
    path('students/<str:student_id>/delete/', views.delete_student, name='delete_student'),
    path('professors/<str:professor_id>/delete/', views.delete_professor, name='delete_professor'),
    
    # Librarian Management
    path('librarians/', views.librarians_list, name='librarians_list'),
    path('import-librarians/', views.import_librarians, name='import_librarians'),
    path('add-librarian/', views.add_librarian, name='add_librarian'),
    path('edit-librarian/<str:librarian_id>/', views.edit_librarian, name='edit_librarian'),
    path('librarians/<str:librarian_id>/delete/', views.delete_librarian, name='delete_librarian'),
    
    # Admin Staff Management (Pre-registration)
    path('admin-staff/', views.admin_staff_list, name='admin_staff_list'),
    path('import-admin-staff/', views.import_admin_staff, name='import_admin_staff'),
    path('add-admin-staff/', views.add_admin_staff, name='add_admin_staff'),
    path('edit-admin-staff/<str:admin_id>/', views.edit_admin_staff, name='edit_admin_staff'),
    path('admin-staff/<str:admin_id>/delete/', views.delete_admin_staff, name='delete_admin_staff'),

    path('thesis/<int:thesis_id>/view/', views.view_thesis, name='view_thesis'),
    path('thesis/<int:thesis_id>/page/<int:page_num>/', views.serve_thesis_page_image, name='serve_thesis_page_image'),
    path('thesis/<int:pk>/restricted/', views.restricted_view_thesis_file, name='restricted_view_thesis_file'),
    path('csrf_failure/', views.csrf_failure, name='csrf_failure'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)