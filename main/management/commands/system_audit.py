from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

class Command(BaseCommand):
    help = 'Runs a full functional audit of the system'

    def handle(self, *args, **options):
        client = Client()
        self.stdout.write(self.style.SUCCESS('--- STARTING SYSTEM AUDIT ---'))

        # 1. Test Homepage
        response = client.get('/')
        self.report("Homepage Accessibility", response.status_code == 200)

        # 2. Find an Admin to test with
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            self.stdout.write(self.style.ERROR("No superuser found to test with!"))
            return

        self.test_view(client, "admin_staff_list", "Admin Staff Management")
        
        # 4. Test Librarian Restrictions (View only, no Add/Edit)
        librarian_user = User.objects.filter(profile__role='librarian').first()
        if librarian_user:
            client.force_login(librarian_user)
            self.stdout.write(self.style.SUCCESS(f"Logged in as Librarian: {librarian_user.username}"))
            
            # Should see lists
            self.test_view(client, "students_list", "Librarian View: Students List")
            
            # Should NOT be able to reach Add Admin page
            res = client.get(reverse('add_admin_staff'))
            self.report("Librarian Restriction: Add Admin Staff", res.status_code in [302, 403], f"Status: {res.status_code} (Redirect/Forbidden expected)")
            
            # Log back in as admin for final checks
            client.force_login(admin)
        else:
            self.stdout.write(self.style.WARNING("No librarian user found to test restrictions."))

        # 5. Test Tabbed Logs
        for tab in ['all', 'security', 'user', 'thesis', 'import']:
            url = reverse('admin_log_entries') + f'?tab={tab}'
            res = client.get(url)
            self.report(f"Audit Tab: {tab.capitalize()}", res.status_code == 200, f"Status: {res.status_code}")

        self.stdout.write(self.style.SUCCESS('--- AUDIT COMPLETE ---'))

    def report(self, name, success, info=""):
        status = "[PASS]" if success else "[FAIL]"
        if success:
            self.stdout.write(self.style.SUCCESS(f"{status} {name} {info}"))
        else:
            self.stdout.write(self.style.ERROR(f"{status} {name} {info}"))

    def test_view(self, client, url_name, label):
        try:
            url = reverse(url_name)
            response = client.get(url)
            self.report(label, response.status_code == 200, f"Status: {response.status_code}")
        except Exception as e:
            self.report(label, False, str(e))
