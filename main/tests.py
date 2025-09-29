from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group, Permission
from django.contrib.admin.models import LogEntry, ADDITION
from django.core.files.uploadedfile import SimpleUploadedFile

from main.models import Thesis, Category, Course, Submission, Department


# ==============================
# TC001 – TC004 (User Access & Search)
# ==============================
class AuthTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="Student01",
            email="Student01@gmail.com",
            password="Student01"
        )

    def test_tc001_login_valid(self):
        response = self.client.post(reverse("login"), {
            "username": "Student01",
            "password": "Student01"
        })
        self.assertEqual(response.status_code, 302)

    def test_tc002_signup_valid(self):
        response = self.client.post(reverse("signup"), {
            "username": "Student02",
            "email": "student02@gmail.com",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        })

        # Only print errors if signup failed
        if response.status_code != 302 and response.context and "form" in response.context:
            print("Signup form errors:", response.context["form"].errors)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="Student02").exists())

class SearchFilterTestCase(TestCase):
    def setUp(self):
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
        # Title
        response = self.client.get(reverse("index"), {"q": "Thesis Library"})
        self.assertContains(response, "Thesis Library")
        # Author
        response = self.client.get(reverse("index"), {"q": "Cayabyab"})
        self.assertContains(response, "Cayabyab")
        # Keyword
        response = self.client.get(reverse("index"), {"q": "Library"})
        self.assertContains(response, "Library")

    def test_tc004_filter_by_category_year_author(self):
        response = self.client.get(reverse("categories"), {
            "year": 2025,
            "author": "Cayabyab",
            "category": self.cat.id
        })
        self.assertContains(response, "Thesis Library")


        # 10 - 12

class AdminPanelTestCase(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin01", "admin@gmail.com", "adminpass")
        self.client.login(username="admin01", password="adminpass")

    def test_tc010_audit_logs(self):
        log = LogEntry.objects.create(
            user=self.admin,
            content_type_id=1,
            object_id="1",
            object_repr="Test Log",
            action_flag=ADDITION,
            change_message="Test Addition"
        )
        self.assertEqual(LogEntry.objects.count(), 1)

    def test_tc011_groups_and_permissions(self):
        group = Group.objects.create(name="Professor")
        perm = Permission.objects.get(codename="add_logentry")
        group.permissions.add(perm)
        self.assertIn(perm, group.permissions.all())

    def test_tc012_create_admin_user(self):
        response = self.client.post(reverse("admin:auth_user_add"), {
            "username": "Admin02",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
            "is_staff": True,
            "is_active": True,
            "is_superuser": True,
        }, follow=True)

        # Only print if there are actual errors
        if response.context and "adminform" in response.context:
            errors = response.context["adminform"].errors
            if errors:
                print("Admin user form errors:", errors)

        self.assertTrue(User.objects.filter(username="Admin02").exists())


