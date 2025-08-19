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
    path('thesis/<int:pk>/', views.thesis_detail, name='thesis_detail'),
    path('thesis/<int:pk>/view/', views.view_thesis_file, name='thesis_view_file'),
    path('thesis/<int:pk>/download/', views.download_thesis_file, name='thesis_download_file'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)