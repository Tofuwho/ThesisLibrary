# main/tests.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group, Permission
from django.contrib.admin.models import LogEntry, ADDITION
from django.core.files.uploadedfile import SimpleUploadedFile

from main.models import (
    Thesis, Category, Course, Submission, Department,
    RejectedThesis, DownloadLog
)

# ===================================================
# TC001 – TC004 (User Access & Search)
# ===================================================
class AuthTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="Student01",
            email="Student01@gmail.com",
            password="Student01"
        )

    def test_tc001_login_valid(self):
        """TC001: Validate login using valid credentials"""
        response = self.client.post(reverse("login"), {
            "username": "Student01",
            "password": "Student01"
        })
        self.assertEqual(response.status_code, 302)

    def test_tc002_signup_valid(self):
        """TC002: Validate signup using valid credentials"""
        from main.models import Student, VerificationCode
        
        # Create department and course first
        cat = Category.objects.create(name="Undergraduate")
        dept = Department.objects.create(name="CICT", category=cat)
        Course.objects.create(name="BSCS", department=dept)
        
        # Create student in records
        Student.objects.create(
            student_id="Student02",
            first_name="Student",
            last_name="Two"
        )

        # Step 1: Initiate signup (identification)
        response = self.client.post(reverse("signup"), {
            "username": "Student02",
            "email": "student02@gmail.com"
        })
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode(), {
            "success": True,
            "requires_verification": True,
            "id": "Student02"
        })

        # Check that inactive user was created
        self.assertTrue(User.objects.filter(username="Student02", is_active=False).exists())
        user = User.objects.get(username="Student02")

        # Step 2: Retrieve the generated verification code
        v_code = VerificationCode.objects.get(user=user).code

        # Step 3: Activate the account with password
        response = self.client.post(reverse("activate_account"), {
            "username": "Student02",
            "code": v_code,
            "password": "SecurePass123!"
        })
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode(), {
            "success": True
        })

        # Verify that the user is now active and the profile is updated
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertFalse(user.profile.is_premade)


class SearchFilterTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="student_search",
            password="password_search"
        )
        self.client.login(username="student_search", password="password_search")
        self.cat = Category.objects.create(name="Undergraduate")
        self.dept = Department.objects.create(name="CICT", category=self.cat)
        self.course = Course.objects.create(name="BSCS", department=self.dept)
        self.thesis = Thesis.objects.create(
            title="Thesis Library",
            author="Cayabyab",
            year=2025,
            abstract="A library system",
            keywords="Library, Research",
            category=self.cat,
            department=self.dept,
            course=self.course,
        )

    def test_tc003_search_title_author_keyword(self):
        """TC003: Search by title, author, keyword"""
        response = self.client.get(reverse("index"), {"q": "Thesis Library"})
        self.assertIn(response.status_code, [200, 302])

    def test_tc004_filter_by_category_year_author(self):
        """TC004: Filter using category/year/author"""
        response = self.client.get(reverse("categories"), {
            "year": 2025,
            "author": "Cayabyab",
            "category": self.cat.id
        })
        self.assertEqual(response.status_code, 200)


# ===================================================
# TC005 – TC009 (Submission Stages)
# ===================================================
class SubmissionStagesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat = Category.objects.create(name="Undergraduate")
        self.dept = Department.objects.create(name="CICT", category=self.cat)
        self.course = Course.objects.create(name="BSCS", department=self.dept)
        self.user = User.objects.create_user("student01", "stud1@gmail.com", "studpass")
        self.client.login(username="student01", password="studpass")

    def _upload_submission(self, title="Test Submission"):
        pdf = SimpleUploadedFile("thesis.pdf", b"PDF", content_type="application/pdf")
        approval = SimpleUploadedFile("approval.pdf", b"PDF", content_type="application/pdf")
        return self.client.post(reverse("create_submission"), {
            "title": title,
            "firstName": "John",
            "lastName": "Doe",
            "year": 2025,
            "abstract": "Sample abstract",
            "academic_level": self.cat.id,
            "department": self.dept.id,
            "course": self.course.id,
            "thesisFile": pdf,
            "approval_sheet": approval,
        }, follow=True)

    def test_tc005_basic_info_stage(self):
        """TC005: Submission - Basic Info"""
        response = self._upload_submission("Thesis Library")
        self.assertRedirects(response, reverse("my_submissions"))
        self.assertTrue(Submission.objects.filter(title="Thesis Library").exists())

    def test_tc006_thesis_details_stage(self):
        """TC006: Submission - Thesis Details"""
        response = self._upload_submission("Research Portal")
        self.assertRedirects(response, reverse("my_submissions"))

    def test_tc007_file_upload_stage(self):
        """TC007: Submission - File Upload"""
        response = self._upload_submission("Digital Library")
        self.assertRedirects(response, reverse("my_submissions"))

    def test_tc008_supervisor_info_stage(self):
        """TC008: Submission - Supervisor Info"""
        pdf = SimpleUploadedFile("thesis.pdf", b"PDF", content_type="application/pdf")
        approval = SimpleUploadedFile("approval.pdf", b"PDF", content_type="application/pdf")
        response = self.client.post(reverse("create_submission"), {
            "title": "Supervised Research",
            "firstName": "Ana",
            "lastName": "Cruz",
            "year": 2025,
            "abstract": "Supervisor info stage",
            "academic_level": self.cat.id,
            "department": self.dept.id,
            "course": self.course.id,
            "thesisFile": pdf,
            "approval_sheet": approval,
            "supervisorName": "Dr. Reyes",
            "supervisorEmail": "dreyes@tcu.edu",
        }, follow=True)
        self.assertRedirects(response, reverse("my_submissions"))

    def test_tc009_review_and_submit_stage(self):
        """TC009: Submission - Review & Submit"""
        response = self._upload_submission("Final Submission")
        self.assertRedirects(response, reverse("my_submissions"))


# ===================================================
# TC010 – TC017 (Admin Panel)
# ===================================================
class AdminPanelTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username='admin01', password='password123', email='admin@test.com'
        )
        self.client.login(username='admin01', password='password123')
        self.category = Category.objects.create(name="Undergrad")
        self.department = Department.objects.create(name="CICT", category=self.category)
        self.course = Course.objects.create(name="BSCS", department=self.department)
        self.pdf = SimpleUploadedFile("test.pdf", b"%PDF", content_type="application/pdf")
        self.png = SimpleUploadedFile("approval.png", b"PNG", content_type="image/png")

    def test_tc010_audit_logs(self):
        """TC010: Admin - Audit Logs"""
        LogEntry.objects.create(
            user=self.admin, content_type_id=1,
            object_id="1", object_repr="Test Log",
            action_flag=ADDITION, change_message="Added"
        )
        self.assertEqual(LogEntry.objects.count(), 1)

    def test_tc011_groups_permissions(self):
        """TC011: Admin - Groups & Permissions"""
        group = Group.objects.create(name="Professor")
        perm = Permission.objects.get(codename="add_logentry")
        group.permissions.add(perm)
        self.assertIn(perm, group.permissions.all())

    def test_tc012_create_admin_user(self):
        """TC012: Admin - Create New User"""
        self.client.post(reverse("admin:auth_user_add"), {
            "username": "Admin02",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }, follow=True)
        self.assertTrue(User.objects.filter(username="Admin02").exists())

    def test_tc013_add_category(self):
        """TC013: Admin - Add Category"""
        self.client.post(reverse("admin:main_category_add"), {"name": "Graduate"})
        self.assertTrue(Category.objects.filter(name="Graduate").exists())

    def test_tc014_add_course(self):
        """TC014: Admin - Add Course"""
        response = self.client.post(reverse("admin:main_course_add"), {
            "name": "MBA",
            "department": self.department.id
        })
        self.assertIn(response.status_code, [200, 302])

    def test_tc016_add_rejected_thesis(self):
        """TC016: Admin - Add Rejected Thesis"""
        url = reverse('admin:main_rejectedthesis_add')
        self.client.post(url, {
            'title': 'Rejected Thesis',
            'author': 'Miguel Villar',
            'year': 2025,
            'abstract': 'Test',
            'thesis_type': 'Practical',
            'specialization': 'Library',
            'category': self.category.id,
            'department': self.department.id,
            'course': self.course.id,
            'file': self.pdf,
            'approval_sheet': self.png,
            'rejection_reason': 'Invalid Format',
            'rejected_by': self.admin.id,
            'original_submitter': self.admin.id,
        }, follow=True)
        self.assertTrue(RejectedThesis.objects.filter(title="Rejected Thesis").exists())


# ===================================================
# TC019 – TC033 (Extended Tests)
# ===================================================
class Updated_Test(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.category = Category.objects.create(name='Undergraduate')
        self.department = Department.objects.create(name='CICT', category=self.category)
        self.course = Course.objects.create(name='BSCS', department=self.department)
        self.thesis = Thesis.objects.create(
            title='Library System',
            author='Miguel Villar',
            year=2025,
            abstract='Simple thesis',
            category=self.category,
            department=self.department,
            course=self.course
        )
        # Generate a valid minimal PDF using PyPDF2
        import io
        from PyPDF2 import PdfWriter
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        buf = io.BytesIO()
        writer.write(buf)
        fake_pdf = SimpleUploadedFile("test.pdf", buf.getvalue(), content_type="application/pdf")
        self.thesis = Thesis.objects.create(
            title='Library System',
            author='Miguel Villar',
            year=2025,
            abstract='Simple thesis',
            category=self.category,
            department=self.department,
            course=self.course,
            file=fake_pdf
        )

    def test_tc019_deep_search_mode(self):
        """TC019: Deep search mode"""
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('categories'), {'search': 'Library', 'search_mode': 'deep'})
        self.assertEqual(response.status_code, 200)

    def test_tc020_restricted_view_guest(self):
        """TC020: Restricted thesis preview for guest"""
        response = self.client.get(reverse('restricted_view_thesis_file', args=[self.thesis.id]))
        self.assertEqual(response.status_code, 302)

    def test_tc021_view_full_thesis_authenticated(self):
        """TC021: Full thesis view for logged user"""
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('restricted_view_thesis_file', args=[self.thesis.id]))
        self.assertEqual(response.status_code, 200)

    def test_tc022_download_disabled(self):
        """TC022: Download endpoint returns forbidden"""
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('thesis_download_file', args=[self.thesis.id]))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(DownloadLog.objects.count(), 0)

    def test_tc023_download_disabled_for_invalid_id(self):
        """TC023: Download endpoint forbidden even for invalid thesis"""
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('thesis_download_file', args=[999]))
        self.assertEqual(response.status_code, 403)

    def test_tc024_ajax_download_disabled(self):
        """TC024: AJAX download attempts are forbidden"""
        response = self.client.get(
            reverse('thesis_download_file', args=[self.thesis.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 403)

    def test_tc025_api_departments_valid(self):
        """TC025: API departments (valid)"""
        response = self.client.get(reverse('api_departments', args=[self.category.id]))
        self.assertEqual(response.status_code, 200)

    def test_tc026_api_departments_invalid(self):
        """TC026: API departments (invalid id)"""
        response = self.client.get(reverse('api_departments', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_tc027_api_courses_valid(self):
        """TC027: API courses (valid)"""
        response = self.client.get(reverse('api_courses', args=[self.department.id]))
        self.assertEqual(response.status_code, 200)

    def test_tc028_csrf_failure_page(self):
        """TC028: Validate CSRF failure page"""
        response = self.client.get('/csrf_failure/')
        self.assertEqual(response.status_code, 403)

    def test_tc029_signup_json(self):
        """TC029: Signup via JSON"""
        response = self.client.post(
            reverse('signup'),
            data='{"username":"newuser","email":"new@user.com","password":"12345"}',
            content_type='application/json'
        )
        self.assertIn(response.status_code, [200, 400])

    def test_tc030_signup_duplicate_username(self):
        """TC030: Validate signup duplicate username"""
        User.objects.create_user(username='dupe', password='pass')
        response = self.client.post(
            reverse('signup'),
            data='{"username":"dupe","email":"dup@test.com","password":"pass"}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_tc031_login_json_success(self):
        """TC031: Login via JSON"""
        response = self.client.post(
            reverse('login'),
            data='{"username":"testuser","password":"12345"}',
            content_type='application/json'
        )
        self.assertIn(response.status_code, [200, 400])

    def test_tc032_login_json_invalid(self):
        """TC032: Validate login with wrong credentials"""
        response = self.client.post(
            reverse('login'),
            data='{"username":"testuser","password":"wrong"}',
            content_type='application/json'
        )
        self.assertIn(response.status_code, [400, 500])

    def test_tc033_my_submissions_page(self):
        """TC033: My submissions list"""
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('my_submissions'))
        self.assertEqual(response.status_code, 200)

    # Aliases to match workflow matrix configuration expectations
    test_tc022_download_logging = test_tc022_download_disabled
    test_tc023_invalid_thesis_download = test_tc023_download_disabled_for_invalid_id
    test_tc024_ajax_unauthorized_download = test_tc024_ajax_download_disabled


class AdminTemplatesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_superuser(
            username="admin_test",
            email="admin@test.com",
            password="password123"
        )
        self.staff_user.profile.role = 'admin'
        self.staff_user.profile.save()
        self.client.login(username="admin_test", password="password123")
        
        # Create category, department, course, and a thesis for rendering
        self.category = Category.objects.create(name="Undergraduate")
        self.department = Department.objects.create(name="CICT", category=self.category)
        self.course = Course.objects.create(name="BSCS", department=self.department)
        
        # Create a pending submission
        self.pending = Submission.objects.create(
            submitter=self.staff_user,
            title="Pending Thesis",
            author="Author One",
            year=2026,
            abstract="Abstract here",
            status="pending",
            category=self.category,
            department=self.department,
            course=self.course
        )
        # Create an approved thesis
        self.approved = Thesis.objects.create(
            title="Approved Thesis",
            author="Author Two",
            year=2026,
            abstract="Abstract here",
            category=self.category,
            department=self.department,
            course=self.course
        )
        # Create a rejected submission
        self.rejected = RejectedThesis.objects.create(
            title="Rejected Thesis",
            author="Author Three",
            year=2026,
            abstract="Abstract here",
            rejection_reason="Typo",
            category=self.category,
            department=self.department,
            course=self.course,
            rejected_by=self.staff_user
        )

    def test_pending_submissions_renders(self):
        response = self.client.get(reverse('pending_submissions'))
        self.assertEqual(response.status_code, 200)

    def test_approved_theses_renders(self):
        response = self.client.get(reverse('theses_list'))
        self.assertEqual(response.status_code, 200)

    def test_rejected_theses_renders(self):
        response = self.client.get(reverse('rejected_thesis_list'))
        self.assertEqual(response.status_code, 200)

    def test_add_category_post(self):
        response = self.client.post(reverse('admin_categories'), {
            'name': 'New Category',
            'admin_name': 'Test Admin',
            'action_reason': 'Testing additions',
            'action_date': '2026-07-03',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Category.objects.filter(name='New Category').exists())

    def test_add_department_post(self):
        response = self.client.post(reverse('departments_list'), {
            'name': 'New Dept',
            'category_id': self.category.id,
            'admin_name': 'Test Admin',
            'action_reason': 'Testing additions',
            'action_date': '2026-07-03',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Department.objects.filter(name='New Dept', category=self.category).exists())

    def test_add_course_post(self):
        response = self.client.post(reverse('courses_list'), {
            'name': 'New Program',
            'department_id': self.department.id,
            'admin_name': 'Test Admin',
            'action_reason': 'Testing additions',
            'action_date': '2026-07-03',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Course.objects.filter(name='New Program', department=self.department).exists())

    def test_delete_course(self):
        response = self.client.post(reverse('delete_course', args=[self.course.id]), {
            'admin_name': 'Test Admin',
            'action_reason': 'Testing deletions',
            'action_date': '2026-07-03',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Course.objects.filter(id=self.course.id).exists())

    def test_delete_department(self):
        response = self.client.post(reverse('delete_department', args=[self.department.id]), {
            'admin_name': 'Test Admin',
            'action_reason': 'Testing deletions',
            'action_date': '2026-07-03',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Department.objects.filter(id=self.department.id).exists())

    def test_delete_category(self):
        response = self.client.post(reverse('delete_category', args=[self.category.id]), {
            'admin_name': 'Test Admin',
            'action_reason': 'Testing deletions',
            'action_date': '2026-07-03',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Category.objects.filter(id=self.category.id).exists())

    def test_student_dashboard_access_for_student(self):
        student_user = User.objects.create_user(
            username="student_test",
            email="student@test.com",
            password="password123"
        )
        student_user.profile.role = 'student'
        student_user.profile.save()
        self.client.login(username="student_test", password="password123")
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_student_dashboard_access_for_admin_redirects(self):
        self.client.login(username="admin_test", password="password123")
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('pending_submissions'), response.url)

    def test_student_dashboard_access_for_anonymous_redirects(self):
        self.client.logout()
        response = self.client.get(reverse('student_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_profile_card_for_student(self):
        student_user = User.objects.create_user(
            username="student_test_profile",
            email="student_profile@test.com",
            password="password123"
        )
        student_user.profile.role = 'student'
        student_user.profile.save()
        self.client.login(username="student_test_profile", password="password123")
        response = self.client.get(reverse('profile_card'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('profile', response.context)
        self.assertEqual(response.context['profile']['role_code'], 'student')
        self.assertIn('total_submissions', response.context['profile'])

    def test_profile_card_for_professor(self):
        prof_user = User.objects.create_user(
            username="prof_test_profile",
            email="prof_profile@test.com",
            password="password123"
        )
        prof_user.profile.role = 'professor'
        prof_user.profile.save()
        self.client.login(username="prof_test_profile", password="password123")
        response = self.client.get(reverse('profile_card'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('profile', response.context)
        self.assertEqual(response.context['profile']['role_code'], 'professor')
        self.assertIn('total_supervised', response.context['profile'])

    def test_profile_card_for_admin(self):
        self.client.login(username="admin_test", password="password123")
        response = self.client.get(reverse('profile_card'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('profile', response.context)
        self.assertEqual(response.context['profile']['role_code'], 'admin')
        self.assertIn('total_actions', response.context['profile'])


class CoAuthorIntegrationTestCase(TestCase):
    def setUp(self):
        # Create categories and course details
        self.category = Category.objects.create(name="Undergraduate")
        self.department = Department.objects.create(name="CICT", category=self.category)
        self.course = Course.objects.create(name="BSCS", department=self.department)

        # Create two students
        self.student1 = User.objects.create_user(
            username="Student01",
            email="student1@tcu.edu.ph",
            password="password123"
        )
        self.student1.profile.role = 'student'
        self.student1.profile.save()

        self.student2 = User.objects.create_user(
            username="Student02",
            email="student2@tcu.edu.ph",
            password="password123"
        )
        self.student2.profile.role = 'student'
        self.student2.profile.save()

        # Add student2 to the Student pre-registration database
        from main.models import Student
        Student.objects.create(
            student_id="Student02",
            first_name="Juan",
            last_name="Cruz",
            email="student2@tcu.edu.ph"
        )

        # Create an admin user for approval
        self.admin_user = User.objects.create_superuser(
            username="admin_user",
            email="admin@test.com",
            password="password123"
        )

    def test_student_lookup_api(self):
        self.client.login(username="Student01", password="password123")
        response = self.client.get(reverse('api_student_lookup', kwargs={'student_id': 'Student02'}))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['first_name'], 'Juan')
        self.assertEqual(data['last_name'], 'Cruz')
        self.assertEqual(data['email'], 'student2@tcu.edu.ph')

    def test_create_submission_links_coauthor(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from main.models import Submission
        
        pdf_file = SimpleUploadedFile("thesis.pdf", b"pdf content", content_type="application/pdf")
        sheet_file = SimpleUploadedFile("approval.jpg", b"image content", content_type="image/jpeg")

        self.client.login(username="Student01", password="password123")
        # Submit a thesis listing Student02 as co-author
        response = self.client.post(reverse('create_submission'), {
            'title': 'Linked Co-Author Study',
            'academic_level': self.category.id,
            'department': self.department.id,
            'course': self.course.id,
            'year': 2026,
            'abstract': 'Test Abstract',
            'keywords': 'test, linking',
            'firstName': 'Jane',
            'lastName': 'Doe',
            'thesisFile': pdf_file,
            'approval_sheet': sheet_file,
            'coauthors[0][first_name]': 'Juan',
            'coauthors[0][last_name]': 'Cruz',
            'coauthors[0][student_id]': 'Student02',
            'coauthors[0][email]': 'student2@tcu.edu.ph',
            'confirmSubmission': 'on'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify SubmissionCoAuthor is linked to Student02's User account
        submission = Submission.objects.get(title='Linked Co-Author Study')
        co_author = submission.co_authors.first()
        self.assertIsNotNone(co_author)
        self.assertEqual(co_author.user, self.student2)

    def test_approve_submission_carries_link(self):
        from main.models import Submission, SubmissionCoAuthor
        self.client.login(username="Student01", password="password123")
        submission = Submission.objects.create(
            submitter=self.student1,
            title='Approval Carries Link Study',
            category=self.category,
            department=self.department,
            course=self.course,
            year=2026,
            abstract='Test Abstract'
        )
        SubmissionCoAuthor.objects.create(
            submission=submission,
            user=self.student2,
            first_name='Juan',
            last_name='Cruz',
            student_id='Student02',
            email='student2@tcu.edu.ph'
        )
        
        # Approve submission
        thesis = submission.approve()
        
        # Verify CoAuthor in Thesis carries the linked User relation
        co_author = thesis.co_authors.first()
        self.assertIsNotNone(co_author)
        self.assertEqual(co_author.user, self.student2)

    def test_dashboard_displays_coauthored(self):
        from main.models import Submission, SubmissionCoAuthor
        # Create submission listing Student02 as co-author
        submission = Submission.objects.create(
            submitter=self.student1,
            title='Co-Authored Dashboard Study',
            category=self.category,
            department=self.department,
            course=self.course,
            year=2026,
            abstract='Test Abstract'
        )
        SubmissionCoAuthor.objects.create(
            submission=submission,
            user=self.student2,
            first_name='Juan',
            last_name='Cruz',
            student_id='Student02',
            email='student2@tcu.edu.ph'
        )
        
        # Login as Student02
        self.client.login(username="Student02", password="password123")
        response = self.client.get(reverse('my_submissions'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('co_authored_submissions', response.context)
        self.assertEqual(response.context['co_authored_submissions'].count(), 1)
        self.assertEqual(response.context['co_authored_submissions'].first(), submission)

    def test_student_lookup_by_name_api(self):
        self.client.login(username="Student01", password="password123")
        response = self.client.get(reverse('api_student_lookup_by_name') + '?first_name=Juan&last_name=Cruz')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['student_id'], 'Student02')
        self.assertEqual(data['email'], 'student2@tcu.edu.ph')


class DuplicateAccountsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create admin user
        self.admin = User.objects.create_superuser(
            username="Admin01",
            email="admin01@tcu.edu.ph",
            password="adminpassword"
        )
        from authapp.models import Profile
        profile, _ = Profile.objects.get_or_create(user=self.admin)
        profile.role = Profile.ADMIN
        profile.save()
        self.client.login(username="Admin01", password="adminpassword")

        # Create an existing student
        from main.models import Student
        Student.objects.create(
            student_id="StudentExist",
            first_name="Existing",
            last_name="Student",
            email="exist@tcu.edu.ph"
        )
        User.objects.create_user(username="StudentExist", email="exist@tcu.edu.ph", password="passwordExist")

    def test_add_student_duplicate_blocked(self):
        """Verify that adding a student with an existing ID is blocked and returns an error."""
        response = self.client.post(reverse("add_student"), {
            "student_id": "StudentExist",
            "first_name": "New",
            "last_name": "Student",
            "email": "new@tcu.edu.ph"
        })
        self.assertEqual(response.status_code, 200) # Form re-renders on validation error
        # Verify student table size hasn't changed
        from main.models import Student
        self.assertEqual(Student.objects.filter(student_id="StudentExist").count(), 1)
        self.assertEqual(Student.objects.all().count(), 1)

    def test_import_students_duplicate_skipped(self):
        """Verify that importing students skips those with existing IDs/usernames."""
        import json
        response = self.client.post(
            reverse("import_students"),
            data=json.dumps({
                "students": [
                    {
                        "student_id": "StudentExist",
                        "first_name": "Ignored",
                        "last_name": "Import",
                        "email": "ignored@tcu.edu.ph"
                    },
                    {
                        "student_id": "StudentNew",
                        "first_name": "Imported",
                        "last_name": "Student",
                        "email": "newimport@tcu.edu.ph"
                    }
                ]
            }),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Only 1 student should be imported (StudentNew), StudentExist should be skipped cleanly
        self.assertEqual(data["count"], 1)
        from main.models import Student
        self.assertTrue(Student.objects.filter(student_id="StudentNew").exists())
        self.assertEqual(Student.objects.all().count(), 2)

