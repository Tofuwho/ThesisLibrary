import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.models import ADDITION
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from ..models import Student, Professor, Librarian, AdminStaff
from authapp.models import Profile
from .admin import log_admin_action
from .auth import create_premade_user

@login_required
@user_passes_test(lambda u: u.is_staff)
def students_list(request):
    students = list(Student.objects.all().order_by('student_id'))
    existing_ids = {s.student_id for s in students}
    orphans = User.objects.filter(profile__role=Profile.STUDENT).exclude(username__in=existing_ids)
    for o in orphans:
        students.append(Student(student_id=o.username, first_name=o.first_name, last_name=o.last_name, email=o.email, created_at=o.date_joined))
    return render(request, 'main/students_list.html', {'students': students})

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def import_students(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid"}, status=400)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Invalid"}, status=400)
    students_data = data.get("students", [])
    created = []
    for s in students_data:
        sid = s.get("student_id")
        if sid and not Student.objects.filter(student_id=sid).exists() and not User.objects.filter(username=sid).exists():
            student = Student.objects.create(student_id=sid, first_name=s.get("first_name"), last_name=s.get("last_name"), email=s.get("email"), created_at=timezone.now())
            created.append(student)
            create_premade_user(sid, s.get("email"), s.get("first_name"), s.get("last_name"), Profile.STUDENT)
    if created:
        log_admin_action(request.user, request.user, ADDITION, f"[BULK IMPORT] Imported {len(created)} student records")
    return JsonResponse({"count": len(created)})

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def add_student(request):
    if request.method == "POST":
        sid = request.POST.get("student_id")
        first, last, email = request.POST.get("first_name"), request.POST.get("last_name"), request.POST.get("email")
        if Student.objects.filter(student_id=sid).exists() or User.objects.filter(username=sid).exists():
            messages.error(request, f"Student ID '{sid}' already exists. Please choose a different ID.")
            return render(request, "main/add_student.html", {
                "student_id": sid, "first_name": first, "last_name": last, "email": email
            })
        Student.objects.create(student_id=sid, first_name=first, last_name=last, email=email)
        create_premade_user(sid, email, first, last, Profile.STUDENT)
        messages.success(request, f"Student account '{sid}' created successfully.")
        return redirect("students_list")
    return render(request, "main/add_student.html")

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def edit_student(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    if request.method == "POST":
        student.first_name, student.last_name, student.email = request.POST.get("first_name"), request.POST.get("last_name"), request.POST.get("email")
        student.save()
        return redirect('students_list')
    return render(request, 'main/edit_student.html', {'student': student})

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def delete_student(request, student_id):
    try:
        student = Student.objects.get(student_id=student_id)
        student.delete()
        messages.success(request, f"Student {student_id} deleted.")
    except Student.DoesNotExist:
        messages.warning(request, f"Student {student_id} has already been deleted or does not exist.")
    return redirect('students_list')

@login_required
@user_passes_test(lambda u: u.is_staff)
def professors_list(request):
    professors = list(Professor.objects.all().order_by('professor_id'))
    existing_ids = {p.professor_id for p in professors}
    orphans = User.objects.filter(profile__role=Profile.PROFESSOR).exclude(username__in=existing_ids)
    for o in orphans:
        professors.append(Professor(professor_id=o.username, first_name=o.first_name, last_name=o.last_name, email=o.email, created_at=o.date_joined))
    return render(request, 'main/professors_list.html', {'professors': professors})

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def add_professor(request):
    if request.method == "POST":
        pid = request.POST.get("professor_id")
        first, last, email = request.POST.get("first_name"), request.POST.get("last_name"), request.POST.get("email")
        if Professor.objects.filter(professor_id=pid).exists() or User.objects.filter(username=pid).exists():
            messages.error(request, f"Professor ID '{pid}' already exists. Please choose a different ID.")
            return render(request, "main/add_professor.html", {
                "professor_id": pid, "first_name": first, "last_name": last, "email": email
            })
        Professor.objects.create(professor_id=pid, first_name=first, last_name=last, email=email)
        create_premade_user(pid, email, first, last, Profile.PROFESSOR)
        messages.success(request, f"Professor account '{pid}' created successfully.")
        return redirect('professors_list')
    return render(request, 'main/add_professor.html')

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def delete_professor(request, professor_id):
    try:
        professor = Professor.objects.get(professor_id=professor_id)
        professor.delete()
        messages.success(request, f"Professor {professor_id} deleted.")
    except Professor.DoesNotExist:
        messages.warning(request, f"Professor {professor_id} has already been deleted or does not exist.")
    return redirect('professors_list')

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def edit_professor(request, professor_id):
    professor = get_object_or_404(Professor, professor_id=professor_id)
    if request.method == "POST":
        professor.first_name, professor.last_name, professor.email = request.POST.get("first_name"), request.POST.get("last_name"), request.POST.get("email")
        professor.save()
        return redirect('professors_list')
    return render(request, 'main/edit_professor.html', {'professor': professor})

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def import_professors(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid"}, status=400)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Invalid"}, status=400)
    items = data.get("professors", [])
    created = []
    for p in items:
        pid = p.get("professor_id")
        if pid and not Professor.objects.filter(professor_id=pid).exists() and not User.objects.filter(username=pid).exists():
            professor = Professor.objects.create(professor_id=pid, first_name=p.get("first_name"), last_name=p.get("last_name"), email=p.get("email"), created_at=timezone.now())
            created.append(professor)
            create_premade_user(pid, p.get("email"), p.get("first_name"), p.get("last_name"), Profile.PROFESSOR)
    if created:
        log_admin_action(request.user, request.user, ADDITION, f"[BULK IMPORT] Imported {len(created)} professor records")
    return JsonResponse({"count": len(created)})

@login_required
@user_passes_test(lambda u: u.is_staff)
def librarians_list(request):
    librarians = list(Librarian.objects.all().order_by('librarian_id'))
    existing_ids = {lib.librarian_id for lib in librarians}
    orphans = User.objects.filter(profile__role=Profile.LIBRARIAN).exclude(username__in=existing_ids)
    for o in orphans:
        librarians.append(Librarian(librarian_id=o.username, first_name=o.first_name, last_name=o.last_name, email=o.email, created_at=o.date_joined))
    return render(request, 'main/librarians_list.html', {'librarians': librarians})

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def add_librarian(request):
    if request.method == "POST":
        lid = request.POST.get("librarian_id")
        first, last, email = request.POST.get("first_name"), request.POST.get("last_name"), request.POST.get("email")
        if Librarian.objects.filter(librarian_id=lid).exists() or User.objects.filter(username=lid).exists():
            messages.error(request, f"Librarian ID '{lid}' already exists. Please choose a different ID.")
            return render(request, 'main/add_librarian.html', {
                "librarian_id": lid, "first_name": first, "last_name": last, "email": email
            })
        Librarian.objects.create(librarian_id=lid, first_name=first, last_name=last, email=email)
        create_premade_user(lid, email, first, last, Profile.LIBRARIAN)
        messages.success(request, f"Librarian account '{lid}' created successfully.")
        return redirect('librarians_list')
    return render(request, 'main/add_librarian.html')

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def edit_librarian(request, librarian_id):
    librarian = get_object_or_404(Librarian, librarian_id=librarian_id)
    if request.method == "POST":
        librarian.first_name, librarian.last_name, librarian.email = request.POST.get("first_name"), request.POST.get("last_name"), request.POST.get("email")
        librarian.save()
        return redirect('librarians_list')
    return render(request, 'main/edit_librarian.html', {'librarian': librarian})

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def delete_librarian(request, librarian_id):
    try:
        librarian = Librarian.objects.get(librarian_id=librarian_id)
        librarian.delete()
        messages.success(request, f"Librarian {librarian_id} deleted.")
    except Librarian.DoesNotExist:
        messages.warning(request, f"Librarian {librarian_id} has already been deleted or does not exist.")
    return redirect('librarians_list')

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def import_librarians(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid"}, status=400)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Invalid"}, status=400)
    items = data.get("librarians", [])
    created = []
    for i in items:
        lid = i.get("librarian_id")
        if lid and not Librarian.objects.filter(librarian_id=lid).exists() and not User.objects.filter(username=lid).exists():
            obj = Librarian.objects.create(librarian_id=lid, first_name=i.get("first_name"), last_name=i.get("last_name"), email=i.get("email"))
            created.append(obj)
            create_premade_user(lid, i.get("email"), i.get("first_name"), i.get("last_name"), Profile.LIBRARIAN)
    if created:
        log_admin_action(request.user, request.user, ADDITION, f"[BULK IMPORT] Imported {len(created)} librarian records")
    return JsonResponse({"count": len(created)})

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_staff_list(request):
    admins = list(AdminStaff.objects.all().order_by('admin_id'))
    existing_ids = {a.admin_id for a in admins}
    orphans = User.objects.filter(profile__role=Profile.ADMIN).exclude(username__in=existing_ids)
    for acc in orphans:
        admins.append(AdminStaff(admin_id=acc.username, first_name=acc.first_name, last_name=acc.last_name, email=acc.email, created_at=acc.date_joined))
    return render(request, 'main/admin_staff_list.html', {'admins': admins})

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def add_admin_staff(request):
    if request.method == "POST":
        aid = request.POST.get("admin_id")
        first, last, email = request.POST.get("first_name"), request.POST.get("last_name"), request.POST.get("email")
        if AdminStaff.objects.filter(admin_id=aid).exists() or User.objects.filter(username=aid).exists():
            messages.error(request, f"Admin ID '{aid}' already exists. Please choose a different ID.")
            return render(request, 'main/add_admin_staff.html', {
                "admin_id": aid, "first_name": first, "last_name": last, "email": email
            })
        AdminStaff.objects.create(admin_id=aid, first_name=first, last_name=last, email=email)
        create_premade_user(aid, email, first, last, Profile.ADMIN)
        messages.success(request, f"Admin account '{aid}' created successfully.")
        return redirect('admin_staff_list')
    return render(request, 'main/add_admin_staff.html')

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def edit_admin_staff(request, admin_id):
    admin = get_object_or_404(AdminStaff, admin_id=admin_id)
    if request.method == "POST":
        admin.first_name, admin.last_name, admin.email = request.POST.get("first_name"), request.POST.get("last_name"), request.POST.get("email")
        admin.save()
        return redirect('admin_staff_list')
    return render(request, 'main/edit_admin_staff.html', {'admin': admin})

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def delete_admin_staff(request, admin_id):
    try:
        admin = AdminStaff.objects.get(admin_id=admin_id)
        admin.delete()
        messages.success(request, f"Admin Staff {admin_id} deleted.")
    except AdminStaff.DoesNotExist:
        messages.warning(request, f"Admin Staff {admin_id} has already been deleted or does not exist.")
    return redirect('admin_staff_list')

@login_required
@user_passes_test(lambda u: hasattr(u, 'profile') and u.profile.role == Profile.ADMIN)
def import_admin_staff(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid"}, status=400)
    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "Invalid"}, status=400)
    items = data.get("admins", [])
    created = []
    for i in items:
        aid = i.get("admin_id")
        if aid and not AdminStaff.objects.filter(admin_id=aid).exists() and not User.objects.filter(username=aid).exists():
            obj = AdminStaff.objects.create(admin_id=aid, first_name=i.get("first_name"), last_name=i.get("last_name"), email=i.get("email"))
            created.append(obj)
            create_premade_user(aid, i.get("email"), i.get("first_name"), i.get("last_name"), Profile.ADMIN)
    if created:
        log_admin_action(request.user, request.user, ADDITION, f"[BULK IMPORT] Imported {len(created)} admin records")
    return JsonResponse({"count": len(created)})
