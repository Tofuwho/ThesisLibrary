from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt  # Only use this temporarily if CSRF is a problem during development
def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('signup_username')
        email = request.POST.get('signup_email')
        password = request.POST.get('signup_password')
        role = request.POST.get('role')

        if not username or not password or not role:
            return JsonResponse({'error': 'Missing required fields'})

        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'})

        user = User.objects.create_user(username=username, email=email, password=password)
        if role == 'admin':
            user.is_staff = True
        user.save()

        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request method'})


@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({'success': True})
        return JsonResponse({'error': 'Invalid credentials'})
    return JsonResponse({'error': 'Invalid request method'})


def logout_view(request):
    logout(request)
    return redirect('/')


def validate_session(request):
    is_logged_in = request.user.is_authenticated
    role = 'admin' if request.user.is_staff else 'student'
    return JsonResponse({'isLoggedIn': is_logged_in, 'role': role if is_logged_in else None})
