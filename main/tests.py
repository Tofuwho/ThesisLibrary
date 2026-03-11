from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from main.models import Thesis, Category, Department, Course, Submission
from authapp.models import Profile

class BasicPagesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create minimal structure
        self.cat = Category.objects.create(name="Undergraduate")
        self.dept = Department.objects.create(name="CICT", category=self.cat)
        self.course = Course.objects.create(name="BSCS", department=self.dept)
        
        # Create a test thesis
        self.thesis = Thesis.objects.create(
            title="Sample Thesis",
            author="John Doe",
            year=2024,
            abstract="This is a test thesis abstract.",
            category=self.cat,
            department=self.dept,
            course=self.course
        )

    def test_landing_page(self):
        """Test that the landing page loads successfully"""
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)

    def test_index_page(self):
        """Test that the index/search page loads successfully"""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sample Thesis")

    def test_categories_page(self):
        """Test that the categories/browse page loads successfully"""
        response = self.client.get(reverse('categories'))
        self.assertEqual(response.status_code, 200)

    def test_thesis_detail(self):
        """Test that the thesis detail page loads successfully"""
        response = self.client.get(reverse('thesis_detail', args=[self.thesis.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sample Thesis")

class SearchTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat = Category.objects.create(name="Undergraduate")
        self.dept = Department.objects.create(name="CICT", category=self.cat)
        self.course = Course.objects.create(name="BSCS", department=self.dept)
        
        Thesis.objects.create(
            title="AI in Library",
            author="Robot",
            year=2024,
            category=self.cat,
            department=self.dept,
            course=self.course
        )
        Thesis.objects.create(
            title="Physics Study",
            author="Einstein",
            year=1905,
            category=self.cat,
            department=self.dept,
            course=self.course
        )

    def test_search_results(self):
        """Test that search identifies the correct thesis"""
        response = self.client.get(reverse('categories'), {'search': 'AI'})
        self.assertContains(response, "AI in Library")
        self.assertNotContains(response, "Physics Study")

class AuthStructureTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='123456', password='password123')
        # Profile is created via signals
        
    def test_profile_setup(self):
        """Test that the profile is correctly created for new users"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertEqual(self.user.profile.role, Profile.STUDENT)
        self.assertTrue(self.user.profile.is_premade is False)
