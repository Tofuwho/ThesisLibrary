from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('about/', views.about_page, name='about'),
    path('views/', views.index_page, name='index'),
    path('categories/', views.categories_page, name='categories'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('thesis/<int:pk>/', views.thesis_detail, name='thesis_detail'),
]
