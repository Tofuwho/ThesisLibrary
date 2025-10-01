from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Group, Permission
from django.contrib.admin.models import LogEntry, ADDITION
from django.core.files.uploadedfile import SimpleUploadedFile

from main.models import Thesis, Category, Course, Submission, Department

#======

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

        # 1 - 2


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

        # 3 - 4

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

    # ==============================
    # TC005 – TC009 (Submission Stages)
    # ==============================
class SubmissionStagesTestCase(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Undergraduate")
        self.dept = Department.objects.create(name="CICT", category=self.cat)
        self.course = Course.objects.create(name="BSCS", department=self.dept)
        self.user = User.objects.create_user("student01", "stud1@gmail.com", "studpass")
        self.client.login(username="student01", password="studpass")  # ✅ ensure logged in

    def debug_response(self, response):
        """Helper to show why test failed."""
        if response.context and "form" in response.context:
            print("Form errors:", response.context["form"].errors)
        else:
            print("No form in response → status:", response.status_code,
                  "| Redirect chain:", response.redirect_chain)

    # 5 - 6

    from django.core.files.uploadedfile import SimpleUploadedFile

    def test_tc005_basic_info_stage(self):
        pdf_file = SimpleUploadedFile("test.pdf", b"PDF content", content_type="application/pdf")
        approval_file = SimpleUploadedFile("approval.pdf", b"PDF content", content_type="application/pdf")

        response = self.client.post(reverse("create_submission"), {
            "title": "Thesis Library",
            "firstName": "John",
            "lastName": "Mark Cayabyab",
            "year": 2025,
            "abstract": "Sample abstract",
            "academic_level": self.cat.id,  # ✅ must match view’s param
            "department": self.dept.id,
            "course": self.course.id,
            "thesisFile": pdf_file,  # ✅ required
            "approval_sheet": approval_file,  # ✅ required
        }, follow=True)

        self.assertRedirects(response, reverse("my_submissions"))
        self.assertTrue(Submission.objects.filter(title="Thesis Library").exists())


    def test_tc006_thesis_details_stage(self):
        pdf_file = SimpleUploadedFile("test2.pdf", b"PDF content", content_type="application/pdf")
        approval_file = SimpleUploadedFile("approval2.pdf", b"PDF content", content_type="application/pdf")

        response = self.client.post(reverse("create_submission"), {
            "title": "Research Portal",
            "firstName": "Jane",
            "lastName": "Doe",
            "year": 2025,
            "abstract": "This is a sample abstract",
            "keywords": "AI, ML, Library",
            "specialization": "Artificial Intelligence",
            "academic_level": self.cat.id,
            "department": self.dept.id,
            "course": self.course.id,
            "thesisFile": pdf_file,
            "approval_sheet": approval_file,
        }, follow=True)

        self.assertRedirects(response, reverse("my_submissions"))
        self.assertTrue(Submission.objects.filter(
            title="Research Portal", specialization="Artificial Intelligence"
        ).exists())

        # 7 - 9

    def test_tc007_file_upload_stage(self):
        file1 = SimpleUploadedFile("thesis.pdf", b"data", content_type="application/pdf")
        file2 = SimpleUploadedFile("approval.pdf", b"data", content_type="application/pdf")

        response = self.client.post(reverse("create_submission"), {
            "title": "Digital Library",
            "firstName": "Mike",
            "lastName": "Villanueva",
            "year": 2025,
            "abstract": "Uploaded file abstract",
            "academic_level": self.cat.id,  # ✅ FIXED
            "department": self.dept.id,
            "course": self.course.id,
            "thesisFile": file1,  # ✅ FIXED
            "approval_sheet": file2,
        }, follow=True)

        self.assertRedirects(response, reverse("my_submissions"))
        self.assertTrue(Submission.objects.filter(title="Digital Library").exists())

    def test_tc008_supervisor_info_stage(self):
        file1 = SimpleUploadedFile("thesis.pdf", b"data", content_type="application/pdf")
        file2 = SimpleUploadedFile("approval.pdf", b"data", content_type="application/pdf")

        response = self.client.post(reverse("create_submission"), {
            "title": "Supervised Research",
            "firstName": "Ana",
            "lastName": "Cruz",
            "year": 2025,
            "abstract": "Supervisor stage abstract",
            "academic_level": self.cat.id,  # ✅ FIXED
            "department": self.dept.id,
            "course": self.course.id,
            "thesisFile": file1,
            "approval_sheet": file2,
            "supervisorName": "Dr. Reyes",  # ✅ FIXED (matches view key)
            "supervisorEmail": "dreyes@tcu.edu",  # ✅ FIXED
            "coSupervisorName": "Prof. Santos",  # ✅ FIXED
            "coSupervisorEmail": "psantos@tcu.edu",  # ✅ FIXED
        }, follow=True)

        self.assertRedirects(response, reverse("my_submissions"))
        self.assertTrue(Submission.objects.filter(
            title="Supervised Research", supervisor_name="Dr. Reyes"
        ).exists())

    def test_tc009_review_and_submit_stage(self):
        file1 = SimpleUploadedFile("thesis.pdf", b"data", content_type="application/pdf")
        file2 = SimpleUploadedFile("approval.pdf", b"data", content_type="application/pdf")

        response = self.client.post(reverse("create_submission"), {
            "title": "Final Submission",
            "firstName": "Luis",
            "lastName": "Dela Cruz",
            "year": 2025,
            "abstract": "Final stage abstract",
            "academic_level": self.cat.id,  # ✅ FIXED
            "department": self.dept.id,
            "course": self.course.id,
            "thesisFile": file1,
            "approval_sheet": file2,
        }, follow=True)

        self.assertRedirects(response, reverse("my_submissions"))
        submission = Submission.objects.get(title="Final Submission")
        self.assertEqual(submission.status, Submission.STATUS_PENDING)

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

        # 13 - 14

    def test_tc013_add_category(self):
        response = self.client.post(reverse("admin:main_category_add"), {
            "name": "Undergraduate"
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Category.objects.filter(name="Undergraduate").exists())

    def test_tc014_add_course(self):
        cat = Category.objects.create(name="Graduate School")
        dept = Department.objects.create(name="Business Dept", category=cat)

        response = self.client.post(reverse("admin:main_course_add"), {
            "name": "Master in Business Administration",
            "department": dept.id
        }, follow=True)

        self.assertTrue(Course.objects.filter(name="Master in Business Administration").exists())

    def test_tc015_add_submission(self):
        cat = Category.objects.create(name="Undergraduate")
        dept = Department.objects.create(name="CICT", category=cat)
        course = Course.objects.create(name="BSCS", department=dept)
        user = User.objects.create_user("student02", "stud2@gmail.com", "studpass")

        file1 = SimpleUploadedFile("file.pdf", b"data", content_type="application/pdf")
        file2 = SimpleUploadedFile("approval.pdf", b"data", content_type="application/pdf")

        response = self.client.post(
            reverse("admin:main_submission_add"),
            {
                "submitter": str(user.id),
                "title": "Thesis Library",
                "author": "Miguel Dennis Villar",
                "year": "2025",
                "abstract": "Thesis Library for TCU",
                "keywords": "Library, Ease-of-Use, Innovation",
                "category": str(cat.id),
                "department": str(dept.id),
                "course": str(course.id),
                "file": file1,
                "approval_sheet": file2,
                "status": Submission.STATUS_PENDING,
                "_save": "1",
            },
            follow=True,
            content_type="multipart/form-data"
        )

        # 🔍 Debug output
        print("Status:", response.status_code)
        print("Redirect chain:", response.redirect_chain)
        if response.context and "adminform" in response.context:
            print("Admin form errors:", response.context["adminform"].errors.as_text())
        else:
            print("No adminform context available")

        # Final check
        self.assertTrue(Submission.objects.filter(title="Thesis Library").exists())

