from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class LoginTestCase(TestCase):
    def setUp(self):
        # Create a user for login
        self.user = User.objects.create_user(
            username="Student01",
            email="Student01@gmail.com",
            password="Student01"
        )

    def test_login_with_valid_credentials(self):
        response = self.client.post(reverse("login"), {
            "username": "Student01",
            "password": "Student01"
        })
        # Check redirect (successful login)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("landing"))
