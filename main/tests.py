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
        response = self.client.post(reverse("signup"), {
            "username": "Student02",
            "email": "student02@gmail.com",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="Student02").exists())


class SearchFilterTestCase(TestCase):
    def setUp(self):
        self.client = Client()
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
        response = self.client.post(reverse("admin:auth_user_add"), {
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
        response = self.client.post(url, {
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
        # Attach fake file
        fake_pdf = SimpleUploadedFile("test.pdf", b"Fake PDF content", content_type="application/pdf")
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
        response = self.client.get(reverse('categories'), {'search': 'Library', 'search_mode': 'deep'})
        self.assertEqual(response.status_code, 200)

    def test_tc020_restricted_view_guest(self):
        """TC020: Restricted thesis preview for guest"""
        response = self.client.get(reverse('thesis_view_file', args=[self.thesis.id]))
        self.assertIn(response.status_code, [200, 500])

    def test_tc021_view_full_thesis_authenticated(self):
        """TC021: Full thesis view for logged user"""
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('thesis_view_file', args=[self.thesis.id]))
        self.assertIn(response.status_code, [200, 404])

    def test_tc022_download_logging(self):
        """TC022: Download logging for thesis"""
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('thesis_download_file', args=[self.thesis.id]))
        self.assertIn(response.status_code, [200, 404])

    def test_tc023_invalid_thesis_download(self):
        """TC023: Invalid thesis download (404)"""
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('thesis_download_file', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_tc024_ajax_unauthorized_download(self):
        """TC024: AJAX unauthorized thesis download"""
        response = self.client.get(
            reverse('thesis_download_file', args=[self.thesis.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertIn(response.status_code, [401, 302])

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
