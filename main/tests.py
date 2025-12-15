# main/tests.py
from django.test import TestCase, Client
from django.urls import reverse, resolve
from main.views import landing_page, about_page, index_page, categories_page, student_dashboard, profile_card, category_detail, create_submission, my_submissions, thesis_detail, download_thesis_file, login_view, signup_view, verify_email_view, forgot_password, reset_password, change_password_profile, api_departments, api_courses, api_extract_abstract, admin_dashboard, admin_log_entries, user_list, delete_user, edit_user, change_password, pending_submissions, approve_thesis, reject_thesis, rejected_thesis_list, theses_list, departments_list, courses_list, students_list, professors_list, import_students, add_student, edit_student, add_professor, edit_professor, import_professors, admin_categories, archive_old_theses, delete_student, delete_professor, view_thesis, serve_thesis_page_image

from django.contrib.auth.models import User, Group, Permission
from django.contrib.admin.models import LogEntry, ADDITION
from django.core.files.uploadedfile import SimpleUploadedFile

from main.models import (
    Thesis, Category,  Submission, Course,
    RejectedThesis, Department, Category
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
            "username": "Student01",
            "email": "student01@gmail.com",
            "password1": "Student01",
        }, follow=False)
        self.assertIn(response.status_code, [301,302])
        self.assertTrue(User.objects.filter(username="Student01").exists())


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

class ChangePasswordTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin", password="adminpass", email="admin@example.com"
        )
        self.user = User.objects.create_user(username="Student01", password="oldPassword123")
        self.client.login(username="admin", password="adminpass")

    def test_tc015_change_password_loads(self):
        """TC049: Change password page loads properly."""
        response = self.client.get(reverse("change_password", args=[self.user.id]))
        self.assertEqual(response.status_code, 200)

    def test_tc017_my_submissions_page(self):
        """TC033: My submissions list"""
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('my_submissions'))
        self.assertEqual(response.status_code, 200)

    def test_tc018_edit_user_form_renders(self):
        """TC048: Edit user page must show the user's old info."""
        response = self.client.get(reverse("edit_user", args=[self.user.id]))
        self.assertContains(response, "Student01")

# ===================================================
# TC019 – TC033 (Extended Tests)
# =================================================
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

    # ===================================================
    # TC020 – TC022 (Public Pages)
    # ===================================================

class LandingPageTests(TestCase):
    def setUp(self):
        self.client = Client()
        from main.models import Category, Department

    def test_tc020_landing_page_loads(self):
        """TC020: Landing page should load successfully."""
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)

    def test_tc021_about_page_loads(self):
        """TC021: About page should load successfully."""
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)

    def test_tc022_categories_page_loads(self):
        """TC022: Categories page should load successfully."""
        response = self.client.get(reverse("categories"))
        self.assertEqual(response.status_code, 200)

    def test_tc023_download_disabled_for_invalid_id(self):
        """TC023: Download endpoint forbidden even for invalid thesis"""
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('thesis_download_file', args=[999]))
        self.assertEqual(response.status_code, 403)

        """TC024"""

    def test_tc025_api_departments_valid(self):
        """TC025: API departments (valid)"""
        category = Category.objects.create(name="Test Category")
        # Create a department belonging to this category
        Department.objects.create(
            name="Test Department",
            category=category
        )
        url = reverse('api_departments', args=[category.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_tc026_api_departments_invalid(self):
        """TC026: API departments (invalid id)"""
        response = self.client.get(reverse('api_departments', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_tc027_api_courses_valid(self):
        """TC027: API courses (valid)"""
        category = Category.objects.create(name="Test Category")
        department = Department.objects.create(name="Dept 1", category=category)
        Course.objects.create(name="Course A", department=department)

        url = reverse("api_courses", args=[department.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

class MySubmissionsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user("stud", "stud@mail.com", "pass123")
        self.other = User.objects.create_user("other", "other@mail.com", "pass123")
        self.category = Category.objects.create(name="Undergrad")
        self.department = Department.objects.create(name="CICT", category=self.category)
        self.course = Course.objects.create(name="BSCS", department=self.department)

    def test_tc028_my_submissions_requires_login(self):
        """TC050: my_submissions should require authentication."""
        response = self.client.get(reverse("my_submissions"))
        self.assertEqual(response.status_code, 302)

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

class UserListTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin",
            password="adminpass",
            email="admin@example.com"
        )
        self.client.login(username="admin", password="adminpass")

    def test_tc033_user_list_page_loads(self):
        """TC034: User list page should load successfully."""
        response = self.client.get(reverse("user_list"))
        self.assertEqual(response.status_code, 200)

    def test_tc034_user_list_displays_users(self):
        """TC035: User list must display existing users."""
        User.objects.create(username="Student01")
        response = self.client.get(reverse("user_list"))
        self.assertContains(response, "Student01")

    def test_tc035_user_list_requires_login(self):
        """TC036: User list should require authentication."""
        self.client.logout()
        response = self.client.get(reverse("user_list"))
        self.assertNotEqual(response.status_code, 200)

    class MySubmissionsTests(TestCase):
        def setUp(self):
            self.client = Client()
            self.user = User.objects.create_user("stud", "stud@mail.com", "pass123")
            self.other = User.objects.create_user("other", "other@mail.com", "pass123")
            self.category = Category.objects.create(name="Undergrad")
            self.department = Department.objects.create(name="CICT", category=self.category)
            self.course = Course.objects.create(name="BSCS", department=self.department)

        def test_tc036_my_submissions_empty(self):
            """TC051: my_submissions should show empty list if no submissions."""
            self.client.login(username="stud", password="pass123")
            response = self.client.get(reverse("my_submissions"))
            self.assertContains(response, "No submissions", status_code=200)


    def test_tc037_user_list_shows_actions(self):
        """TC038: User list should show edit and delete buttons."""
        response = self.client.get(reverse("user_list"))
        self.assertContains(response, "Edit")
        self.assertContains(response, "Delete")

class StudentsListTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin", password="adminpass", email="admin@example.com"
        )
        self.client.login(username="admin", password="adminpass")

    def test_tc038_students_list_loads(self):
        """TC038: Students list page loads properly."""
        response = self.client.get(reverse("students_list"))
        self.assertEqual(response.status_code, 200)

    def test_tc039_professors_list_loads(self):
        """TC039: Professors list page loads properly."""
        response = self.client.get(reverse("professors_list"))
        self.assertEqual(response.status_code, 200)


class ThesisDetailTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Undergrad")
        self.department = Department.objects.create(name="CICT", category=self.category)
        self.course = Course.objects.create(name="BSCS", department=self.department)
        self.thesis = Thesis.objects.create(
            title="AI Research",
            author="John Doe",
            year=2024,
            abstract="Test",
            category=self.category,
            department=self.department,
            course=self.course
        )

    def test_tc041_thesis_detail_loads(self):
        """TC055: thesis_detail loads properly."""
        response = self.client.get(reverse("thesis_detail", args=[self.thesis.id]))
        self.assertEqual(response.status_code, 200)

    def test_tc042_thesis_detail_displays_info(self):
        """TC056: thesis_detail must display thesis contents."""
        response = self.client.get(reverse("thesis_detail", args=[self.thesis.id]))
        self.assertContains(response, "AI Research")

    def test_tc043_thesis_detail_invalid_id(self):
        """TC057: Invalid thesis id returns 404."""
        response = self.client.get(reverse("thesis_detail", args=[9999]))
        self.assertEqual(response.status_code, 404)

# ===================================================
# TC044 – TC047 Edit User Tests
# ===================================================
class EditUserTests(TestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin", password="adminpass", email="admin@example.com"
        )
        self.user = User.objects.create(username="Student01", email="old@mail.com")
        self.client.login(username="admin", password="adminpass")

    def test_tc044_edit_user_loads(self):
        response = self.client.get(reverse("edit_user", args=[self.user.id]))
        self.assertEqual(response.status_code, 200)

    def test_tc045_edit_user_updates_info(self):
        response = self.client.post(reverse("edit_user", args=[self.user.id]), {
            "username": "UpdatedUser",
            "email": "new@mail.com"
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "UpdatedUser")

    def test_tc046_edit_user_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("edit_user", args=[self.user.id]))
        self.assertNotEqual(response.status_code, 200)

    def test_tc047_edit_user_invalid_id(self):
        response = self.client.get(reverse("edit_user", args=[999]))
        self.assertEqual(response.status_code, 404)

# ===================================================
# TC048 – TC052 View Thesis File Tests
# ===================================================



# ===================================================
# TC053 – TC054 (Admin Pages)
# ===================================================
class AdminCategoriesTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin", password="adminpass", email="admin@example.com"
        )
        self.client.login(username="admin", password="adminpass")

    def test_tc053_admin_categories_loads(self):
        """TC053: Admin categories page loads properly."""
        response = self.client.get(reverse("admin_categories"))
        self.assertEqual(response.status_code, 200)



class LandingAboutIndexTests(TestCase):
    def setUp(self):
            self.client = Client()
            self.user = User.objects.create_user(
                username="Student01",
                email="Student01@gmail.com",
                password="Student01"
            )

    def test_TC055_landing_page_loads(self):
        """TC055: Validate landing page loads successfully."""
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "main/landing.html")

    # -------------------------------
    # TC056 – Landing Page Content Check
    # -------------------------------
    def test_TC056_landing_page_contains_content(self):
        """TC056: Validate landing page displays expected content."""
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)
        # Adjust depending on your actual landing page heading
        self.assertContains(response, "Welcome")

    def test_TC057_about_page_loads(self):
        """TC057: Validate about page loads successfully."""
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "main/about.html")

    def test_TC058_about_page_contains_text(self):
        """TC058: Verify about page displays content."""
        response = self.client.get(reverse("about"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "About")

    def test_TC059_student_dashboard_loads(self):
        """TC059: Validate student dashboard page loads successfully."""
        # Log in the test user
        self.client.login(username="Student01", password="Student01")
        response = self.client.get(reverse("student_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "main/student_dashboard.html")

    def test_TC060_student_dashboard_contains_categories(self):
        """TC060: Validate student dashboard displays categories."""
        # Create some test categories
        Category.objects.create(name="Category A")
        Category.objects.create(name="Category B")

        # Log in the test user
        self.client.login(username="Student01", password="Student01")
        response = self.client.get(reverse("student_dashboard"))

        self.assertEqual(response.status_code, 200)
        # Check that categories appear in the response
        self.assertContains(response, "Category A")
        self.assertContains(response, "Category B")

class TestUrls(TestCase):

    def test_TC061_landing_page_loads(self):
        url = reverse("landing")
        self.assertEqual(resolve(url).func, landing_page)

    def test_TC062_about_page_loads(self):
        url = reverse("about")
        self.assertEqual(resolve(url).func, about_page)

    def test_TC063_index_page_loads(self):
        url = reverse("index")
        self.assertEqual(resolve(url).func, index_page)

    def test_TC064_categories_loads(self):
        url = reverse("categories")
        self.assertEqual(resolve(url).func, categories_page)

    def test_TC065_student_dashboard(self):
        url = reverse("student_dashboard")
        self.assertEqual(resolve(url).func, student_dashboard)

    def test_TC066_profile_card(self):
        url = reverse("profile_card")
        self.assertEqual(resolve(url).func, profile_card)

    def test_TC067_category_detail(self):
        url = reverse("category_detail", args=[1])
        self.assertEqual(resolve(url).func, category_detail)

    def test_TC068_create_submission(self):
        url = reverse("create_submission")
        self.assertEqual(resolve(url).func, create_submission)

    def test_TC069_my_submissions(self):
        url = reverse("my_submissions")
        self.assertEqual(resolve(url).func, my_submissions)

    def test_TC070_thesis_detail(self):
        url = reverse("thesis_detail", args=[1])
        self.assertEqual(resolve(url).func, thesis_detail)

    def test_TC071_download_thesis_file(self):
        url = reverse("thesis_download_file", args=[1])
        self.assertEqual(resolve(url).func, download_thesis_file)

    def test_TC072_login_view(self):
        url = reverse("login")
        self.assertEqual(resolve(url).func, login_view)

    def test_TC073_signup_view(self):
        url = reverse("signup")
        self.assertEqual(resolve(url).func, signup_view)

    def test_TC074_verify_email(self):
        url = reverse("verify_email")
        self.assertEqual(resolve(url).func, verify_email_view)

    def test_TC075_forgot_password(self):
        url = reverse("forgot_password")
        self.assertEqual(resolve(url).func, forgot_password)

    def test_TC076_reset_password(self):
        url = reverse("reset_password")
        self.assertEqual(resolve(url).func, reset_password)

    def test_TC077_change_password_profile(self):
        url = reverse("change_password_profile")
        self.assertEqual(resolve(url).func, change_password_profile)

    def test_TC078_api_departments(self):
        url = reverse("api_departments", args=[1])
        self.assertEqual(resolve(url).func, api_departments)

    def test_TC079_api_courses(self):
        url = reverse("api_courses", args=[1])
        self.assertEqual(resolve(url).func, api_courses)

    def test_TC080_api_extract_abstract(self):
        url = reverse("api_extract_abstract")
        self.assertEqual(resolve(url).func, api_extract_abstract)

    def test_TC081_admin_dashboard(self):
        url = reverse("admin_dashboard")
        self.assertEqual(resolve(url).func, admin_dashboard)

    def test_TC082_admin_log_entries(self):
        url = reverse("admin_log_entries")
        self.assertEqual(resolve(url).func, admin_log_entries)

    def test_TC083_user_list(self):
        url = reverse("user_list")
        self.assertEqual(resolve(url).func, user_list)

    def test_TC084_delete_user(self):
        url = reverse("delete_user", args=[1])
        self.assertEqual(resolve(url).func, delete_user)

    def test_TC085_edit_user(self):
        url = reverse("edit_user", args=[1])
        self.assertEqual(resolve(url).func, edit_user)

    def test_TC086_change_password(self):
        url = reverse("change_password", args=[1])
        self.assertEqual(resolve(url).func, change_password)

    def test_TC087_pending_submissions(self):
        url = reverse("pending_submissions")
        self.assertEqual(resolve(url).func, pending_submissions)

    def test_TC088_approve_thesis(self):
        url = reverse("approve_thesis", args=[1])
        self.assertEqual(resolve(url).func, approve_thesis)

    def test_TC089_reject_thesis(self):
        url = reverse("reject_thesis", args=[1])
        self.assertEqual(resolve(url).func, reject_thesis)

    def test_TC090_rejected_thesis_list(self):
        url = reverse("rejected_thesis_list")
        self.assertEqual(resolve(url).func, rejected_thesis_list)

    def test_TC091_theses_list(self):
        url = reverse("theses_list")
        self.assertEqual(resolve(url).func, theses_list)

    def test_TC092_departments_list(self):
        url = reverse("departments_list")
        self.assertEqual(resolve(url).func, departments_list)

    def test_TC093_courses_list(self):
        url = reverse("courses_list")
        self.assertEqual(resolve(url).func, courses_list)

    def test_TC094_students_list(self):
        url = reverse("students_list")
        self.assertEqual(resolve(url).func, students_list)

    def test_TC095_professors_list(self):
        url = reverse("professors_list")
        self.assertEqual(resolve(url).func, professors_list)

    def test_TC096_import_students(self):
        url = reverse("import_students")
        self.assertEqual(resolve(url).func, import_students)

    def test_TC097_add_student(self):
        url = reverse("add_student")
        self.assertEqual(resolve(url).func, add_student)

    def test_TC098_edit_student(self):
        url = reverse("edit_student", args=[1])
        self.assertEqual(resolve(url).func, edit_student)

    def test_TC099_add_professor(self):
        url = reverse("add_professor")
        self.assertEqual(resolve(url).func, add_professor)

    def test_TC100_edit_professor(self):
        url = reverse("edit_professor", args=[1])
        self.assertEqual(resolve(url).func, edit_professor)

    def test_TC101_import_professors(self):
        url = reverse("import_professors")
        self.assertEqual(resolve(url).func, import_professors)

    def test_TC102_admin_categories(self):
        url = reverse("admin_categories")
        self.assertEqual(resolve(url).func, admin_categories)

    def test_TC103_archive_old_theses(self):
        url = reverse("archive_old_theses")
        self.assertEqual(resolve(url).func, archive_old_theses)

    def test_TC104_delete_student(self):
        url = reverse("delete_student", args=[1])
        self.assertEqual(resolve(url).func, delete_student)

    def test_TC105_delete_professor(self):
        url = reverse("delete_professor", args=[1])
        self.assertEqual(resolve(url).func, delete_professor)

    def test_TC106_view_thesis(self):
        url = reverse("view_thesis", args=[1])
        self.assertEqual(resolve(url).func, view_thesis)

    def test_TC107_serve_thesis_page_image(self):
        url = reverse("serve_thesis_page_image", args=[1, 1])
        self.assertEqual(resolve(url).func, serve_thesis_page_image)
