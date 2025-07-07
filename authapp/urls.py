from django.urls import path
from .views import login_view, signup_view, logout_view, validate_session

urlpatterns = [
    path('login/', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('logout/', logout_view, name='logout'),  # ← Add this
    path('validate-session/', validate_session),
]
