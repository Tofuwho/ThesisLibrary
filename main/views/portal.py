import traceback
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone

from ..models import Thesis, Category, Submission, Student, Professor, Department, Course, SubmissionCoAuthor
from authapp.models import Profile
from ..utils import extract_title_from_pdf, extract_abstract_from_pdf

@login_required
def profile_card(request):
    """Display a simple profile card for the logged-in user."""
    user = request.user
    student_record = Student.objects.filter(student_id=user.username).first()
    professor_record = Professor.objects.filter(professor_id=user.username).first()

    def build_name():
        if student_record:
            return f"{student_record.first_name or ''} {student_record.last_name or ''}".strip()
        if professor_record:
            return f"{professor_record.first_name or ''} {professor_record.last_name or ''}".strip()
        if user.first_name or user.last_name:
            return f"{user.first_name or ''} {user.last_name or ''}".strip()
        return user.username

    full_name = build_name()
    contact_email = (
        (student_record.email if student_record and student_record.email else None)
        or (professor_record.email if professor_record and professor_record.email else None)
        or user.email
    )
    identifier = (
        student_record.student_id if student_record else
        professor_record.professor_id if professor_record else
        user.username
    )
    profile_obj, _ = Profile.objects.get_or_create(user=user)
    role = profile_obj.get_role_display()

    submissions_qs = Submission.objects.filter(submitter=user)
    recent_submission = submissions_qs.order_by('-created_at').first()

    initials = ''.join([part[0] for part in full_name.split() if part])[:2].upper()
    if not initials:
        initials = (user.username[:2] or "??").upper()

    profile = {
        "full_name": full_name,
        "role": role,
        "role_code": profile_obj.role,
        "username": user.username,
        "identifier": identifier,
        "email": contact_email or "Not provided",
        "joined": user.date_joined,
        "last_login": user.last_login,
        "submission_count": submissions_qs.count(),
        "recent_submission_title": recent_submission.title if recent_submission else None,
        "recent_submission_date": recent_submission.created_at if recent_submission else None,
        "initials": initials,
        "is_admin": profile_obj.role in [Profile.ADMIN, Profile.LIBRARIAN],
        "has_dashboard": profile_obj.role not in [Profile.ADMIN, Profile.LIBRARIAN],
    }

    return render(request, 'main/profile_card.html', {"profile": profile})

@login_required
def student_dashboard(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != Profile.STUDENT:
        role = request.user.profile.role if hasattr(request.user, 'profile') else None
        if role in [Profile.ADMIN, Profile.LIBRARIAN]:
            return redirect('pending_submissions')
        messages.error(request, "Access denied. Only student accounts can access the thesis submission portal.")
        return redirect('/')
        
    categories = Category.objects.all().order_by('name')
    
    user_data = {
        'first_name': '',
        'last_name': '',
        'email': '',
        'student_id': ''
    }
    
    user_id = request.user.username
    
    try:
        student = Student.objects.get(student_id=user_id)
        user_data['first_name'] = student.first_name or ''
        user_data['last_name'] = student.last_name or ''
        user_data['email'] = student.email or request.user.email or ''
        user_data['student_id'] = student.student_id
    except Student.DoesNotExist:
        try:
            professor = Professor.objects.get(professor_id=user_id)
            user_data['first_name'] = professor.first_name or ''
            user_data['last_name'] = professor.last_name or ''
            user_data['email'] = professor.email or request.user.email or ''
            user_data['student_id'] = professor.professor_id
        except Professor.DoesNotExist:
            user_data['first_name'] = request.user.first_name or ''
            user_data['last_name'] = request.user.last_name or ''
            user_data['email'] = request.user.email or ''
            user_data['student_id'] = user_id
    
    return render(request, 'main/student_dashboard.html', {
        'categories': categories,
        'user_data': user_data,
        'user_role': request.user.profile.role if hasattr(request.user, 'profile') else 'student'
    })

@login_required
@require_POST
def create_submission(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != Profile.STUDENT:
        role = request.user.profile.role if hasattr(request.user, 'profile') else None
        if role in [Profile.ADMIN, Profile.LIBRARIAN]:
            return redirect('pending_submissions')
        messages.error(request, "Access denied. Only student accounts can submit theses.")
        return redirect('/')

    title = request.POST.get('thesisTitle') or request.POST.get('title')
    abstract = request.POST.get('abstract', '')
    keywords = request.POST.get('keywords', '')
    research_category = request.POST.get('research_category', '')
    specialization = request.POST.get('specialization', '')
    year = request.POST.get('year')
    academic_level_id = request.POST.get('academic_level')
    department_id = request.POST.get('department')
    course_id = request.POST.get('course')
    thesis_file = request.FILES.get('thesisFile')
    approval_sheet = request.FILES.get('approval_sheet')

    errors = []
    if not title: errors.append('Title is required')
    if not thesis_file: errors.append('Thesis PDF is required')
    if not approval_sheet: errors.append('Approval sheet is required')
    if not academic_level_id: errors.append('Academic Level is required')
    if not department_id: errors.append('Department is required')
    if not course_id: errors.append('Course/Program is required')

    if errors:
        messages.error(request, 'Please correct the following errors: ' + ', '.join(errors))
        return redirect('student_dashboard')

    try:
        academic_level = Category.objects.get(id=academic_level_id) if academic_level_id else None
        department = Department.objects.get(id=department_id) if department_id else None
        course = Course.objects.get(id=course_id) if course_id else None
    except (Category.DoesNotExist, Department.DoesNotExist, Course.DoesNotExist):
        messages.error(request, 'Invalid academic structure selection')
        return redirect('student_dashboard')

    try:
        co_authors_data = []
        i = 0
        while True:
            first = request.POST.get(f'coauthors[{i}][first_name]', '').strip()
            last = request.POST.get(f'coauthors[{i}][last_name]', '').strip()
            sid = request.POST.get(f'coauthors[{i}][student_id]', '').strip()
            email = request.POST.get(f'coauthors[{i}][email]', '').strip()
            if not any([first, last, sid, email]): break
            co_authors_data.append({'first_name': first, 'last_name': last, 'student_id': sid, 'email': email})
            i += 1

        supervisor_name = request.POST.get('supervisorName', '').strip()
        supervisor_email = request.POST.get('supervisorEmail', '').strip()
        supervisor_department = request.POST.get('supervisorDepartment', '').strip()
        supervisor_title = request.POST.get('supervisorTitle', '').strip()
        co_supervisor_name = request.POST.get('coSupervisorName', '').strip()
        co_supervisor_email = request.POST.get('coSupervisorEmail', '').strip()

        if not title or title.strip() == '':
            if thesis_file:
                try:
                    extracted_title = extract_title_from_pdf(thesis_file)
                    if extracted_title: title = extracted_title
                except Exception: pass
        
        if not abstract or abstract.strip() == '':
            if thesis_file:
                try:
                    extracted_abstract = extract_abstract_from_pdf(thesis_file)
                    if extracted_abstract: abstract = extracted_abstract
                except Exception: pass

        submission = Submission.objects.create(
            submitter=request.user,
            title=title.strip(),
            author=f"{request.POST.get('firstName', '').strip()} {request.POST.get('lastName', '').strip()}".strip(),
            year=int(year) if year and str(year).isdigit() else None,
            abstract=abstract,
            keywords=keywords,
            research_category=research_category,
            specialization=specialization,
            category=academic_level,
            department=department,
            course=course,
            file=thesis_file,
            approval_sheet=approval_sheet,
            supervisor_name=supervisor_name,
            supervisor_email=supervisor_email,
            supervisor_department=supervisor_department,
            supervisor_title=supervisor_title,
            co_supervisor_name=co_supervisor_name,
            co_supervisor_email=co_supervisor_email,
            status=Submission.STATUS_PENDING,
        )
        
        for coauthor_data in co_authors_data:
            SubmissionCoAuthor.objects.create(
                submission=submission,
                first_name=coauthor_data['first_name'],
                last_name=coauthor_data['last_name'],
                student_id=coauthor_data['student_id'],
                email=coauthor_data['email'],
            )
        
        messages.success(request, f'Thesis "{submission.title}" submitted successfully!')
        return redirect('my_submissions')
    except Exception as e:
        messages.error(request, f'Error submitting thesis: {str(e)}')
        return redirect('student_dashboard')

@login_required
def my_submissions(request):
    if not hasattr(request.user, 'profile') or request.user.profile.role != Profile.STUDENT:
        role = request.user.profile.role if hasattr(request.user, 'profile') else None
        if role in [Profile.ADMIN, Profile.LIBRARIAN]:
            return redirect('pending_submissions')
        messages.error(request, "Access denied. Only student accounts can view submissions.")
        return redirect('/')

    submissions = Submission.objects.filter(submitter=request.user)
    return render(request, 'main/my_submissions.html', {'submissions': submissions})
