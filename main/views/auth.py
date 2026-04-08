import json
import random
import string
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.models import ADDITION, CHANGE
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_protect

from ..models import Student, Professor, Librarian, AdminStaff, VerificationCode, PasswordResetCode
from authapp.models import Profile

def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

def create_premade_user(username, email, first_name="", last_name="", role=Profile.STUDENT):
    user = User.objects.filter(username=username).first()
    if not user:
        from django.utils.crypto import get_random_string
        temporary_password = get_random_string(32)
        user = User.objects.create_user(username=username, email=email or "", password=temporary_password, first_name=first_name, last_name=last_name, is_active=False)
    profile, _ = Profile.objects.get_or_create(user=user)
    if profile.is_premade or not user.is_active:
        profile.role = role
        profile.is_premade = True
        profile.must_change_password = True
        profile.save()
        is_staff = (role in [Profile.ADMIN, Profile.LIBRARIAN])
        is_superuser = (role == Profile.ADMIN)
        if user.is_staff != is_staff or user.is_superuser != is_superuser:
            User.objects.filter(id=user.id).update(is_staff=is_staff, is_superuser=is_superuser)
    return user

def send_verification_email(user, code):
    subject = 'Thesis Library - Email Verification Code'
    message = f'Hello {user.username},\nYour code is: {code}\nExpires in 24h.'
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        return True
    except: return False

def send_password_reset_email(user, code):
    subject = 'Thesis Library - Password Reset Code'
    message = f'Hello {user.username},\nYour reset code is: {code}\nExpires in 1h.'
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        return True
    except: return False

@csrf_protect
def login_view(request):
    if request.method == 'POST':
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            uid, pwd = data.get('username'), data.get('password')
            user = authenticate(request, username=uid, password=pwd)
            if user:
                if not user.is_active: return JsonResponse({'success': False, 'error': 'Account inactive.'}, status=400)
                try:
                    if hasattr(user, 'verificationcode') and not user.verificationcode.is_verified:
                        return JsonResponse({'success': False, 'error': 'Not verified.'}, status=400)
                except VerificationCode.DoesNotExist: pass
                login(request, user)
                return JsonResponse({'success': True})
            return JsonResponse({'success': False, 'error': 'Invalid credentials'}, status=400)
        else:
            uid, pwd = request.POST.get('username'), request.POST.get('password')
            user = authenticate(request, username=uid, password=pwd)
            if user and user.is_active:
                login(request, user)
                if is_ajax:
                    return JsonResponse({'success': True, 'redirect_url': request.POST.get('next') or '/'})
                return redirect(request.POST.get('next') or '/')
            
            if is_ajax:
                return JsonResponse({'success': False, 'errors': {'__all__': ['Invalid ID or password.']}}, status=400)
            
            messages.error(request, 'Invalid ID or password.')
    return redirect('/')

@csrf_protect
def signup_view(request):
    if request.method != 'POST': return JsonResponse({"success": False}, status=405)
    data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
    uid, email, pwd, action = data.get("id") or data.get("username"), data.get("email"), data.get("password"), data.get("action")
    if not uid: return JsonResponse({"success": False, "error": "ID required"}, status=400)

    if action == "activate_premade":
        try:
            user = User.objects.get(username=uid)
            user.set_password(pwd); user.is_active = True; user.save()
            user.profile.is_premade = False; user.profile.save()
            VerificationCode.objects.get_or_create(user=user, defaults={'code':'000000','expires_at':timezone.now()+timezone.timedelta(days=365),'is_verified':True})
            return JsonResponse({"success": True})
        except User.DoesNotExist: return JsonResponse({"success": False}, status=404)

    student = Student.objects.filter(student_id=uid).first()
    professor = Professor.objects.filter(professor_id=uid).first()
    librarian = Librarian.objects.filter(librarian_id=uid).first()
    admin_staff = AdminStaff.objects.filter(admin_id=uid).first()
    if not any([student, professor, librarian, admin_staff]): return JsonResponse({"success": False, "error": "ID not found"}, status=400)
    
    try:
        user = User.objects.get(username=uid)
        if getattr(user.profile, 'is_premade', False):
            return JsonResponse({"success": True, "requires_activation": True, "id": uid, "email": email})
    except User.DoesNotExist:
        user = User.objects.create_user(username=uid, email=email, password=pwd, is_active=True)
        if professor: user.profile.role = Profile.PROFESSOR
        elif librarian: user.profile.role = Profile.LIBRARIAN; user.is_staff = True
        elif admin_staff: user.profile.role = Profile.ADMIN; user.is_staff = True; user.is_superuser = True
        user.profile.save(); user.save()
        VerificationCode.objects.create(user=user, code='000000', expires_at=timezone.now()+timezone.timedelta(days=365), is_verified=True)
        return JsonResponse({"success": True})
    return JsonResponse({"success": True})

@csrf_protect
def verify_email_view(request):
    if request.method == 'POST':
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        uid, code = data.get('id') or data.get('username'), data.get('code')
        try:
            user = User.objects.get(username=uid)
            v = VerificationCode.objects.get(user=user)
            if v.code == code and not v.is_expired():
                v.is_verified = True; v.save(); user.is_active = True; user.save()
                return JsonResponse({'success': True})
        except: pass
    return JsonResponse({'success': False}, status=400)

@csrf_protect
def forgot_password(request):
    if request.method == 'POST':
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        uid, email = data.get('id') or data.get('username'), data.get('email')
        try:
            user = User.objects.get(username=uid, email=email)
            code = generate_verification_code()
            PasswordResetCode.objects.filter(user=user, is_used=False).update(is_used=True)
            PasswordResetCode.objects.create(user=user, code=code, expires_at=timezone.now()+timezone.timedelta(hours=1))
            send_password_reset_email(user, code)
        except: pass
        # In offline LAN, we inform the user to visit the Librarian
        return JsonResponse({
            'success': True, 
            'message': 'Reset request recorded. Please visit the library counter with your ID to receive your 6-digit reset code.'
        })
    return redirect('/')

@csrf_protect
def reset_password(request):
    if request.method == 'POST':
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        uid, code, pwd = data.get('id') or data.get('username'), data.get('code'), data.get('new_password')
        try:
            user = User.objects.get(username=uid)
            rc = PasswordResetCode.objects.filter(user=user, is_used=False, code=code).first()
            if rc and not rc.is_expired():
                user.set_password(pwd); user.save(); rc.is_used = True; rc.save()
                return JsonResponse({'success': True})
        except: pass
    return JsonResponse({'success': False}, status=400)

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def change_password(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        new, confirm = data.get('new_password'), data.get('confirm_password')
        if new == confirm:
            user.set_password(new); user.save()
            return JsonResponse({'success': True}) if request.content_type == 'application/json' else redirect('user_list')
    return redirect('user_list')

@login_required
def change_password_profile(request):
    if request.method == 'POST':
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        old, new = data.get('old_password'), data.get('new_password')
        if request.user.check_password(old):
            request.user.set_password(new); request.user.save()
            return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)
