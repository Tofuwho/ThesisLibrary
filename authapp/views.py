import json
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse


def signup_view(request):
    if request.method != 'POST':
        return redirect('/')

    # Handle both AJAX (JSON) and traditional POST
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            username = data.get('id')
            email = data.get('email')
            password = data.get('password')
            role = data.get('role', 'student')
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    else:
        username = request.POST.get('signup_username')
        email = request.POST.get('signup_email')
        password = request.POST.get('signup_password')
        role = request.POST.get('role', 'student')

    if not username or not password:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        messages.error(request, 'Missing required fields')
        return redirect('/')

    if User.objects.filter(username=username).exists():
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Username already exists'})
        messages.error(request, 'Username already exists')
        return redirect('/')

    user = User.objects.create_user(username=username, email=email, password=password)
    if role == 'admin':
        user.is_staff = True
    user.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Account created successfully. You can now log in.'})
    
    messages.success(request, 'Account created successfully. You can now log in.')
    return redirect('/')


def login_view(request):
    if request.method != 'POST':
        return redirect('/')

    username = request.POST.get('username')
    password = request.POST.get('password')

    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        login(request, user)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'redirect_url': '/'})
        messages.success(request, 'Logged in successfully.')
        return redirect('/')
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'errors': {'__all__': ['Invalid credentials.']}})
    
    messages.error(request, 'Invalid credentials.')
    return redirect('/')


def logout_view(request):
    logout(request)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'redirect_url': '/'})
    messages.success(request, 'Logged out successfully.')
    return redirect('/')


def validate_session(request):
    is_logged_in = request.user.is_authenticated
    role = 'admin' if request.user.is_staff else 'student'
    return JsonResponse({'isLoggedIn': is_logged_in, 'role': role if is_logged_in else None})
