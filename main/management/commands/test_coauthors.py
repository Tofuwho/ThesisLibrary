from django.core.management.base import BaseCommand
from main.models import Thesis, CoAuthor, Category, Department, Course
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Test co-author functionality'

    def handle(self, *args, **options):
        self.stdout.write('Testing co-author functionality...')
        
        # Create test data if it doesn't exist
        try:
            # Create a test thesis
            thesis = Thesis.objects.first()
            if not thesis:
                self.stdout.write('No thesis found. Creating test data...')
                
                # Create test category, department, course
                category, created = Category.objects.get_or_create(name="Test Category")
                department, created = Department.objects.get_or_create(
                    name="Test Department", 
                    category=category
                )
                course, created = Course.objects.get_or_create(
                    name="Test Course", 
                    department=department
                )
                
                # Create test thesis
                thesis = Thesis.objects.create(
                    title="Test Thesis",
                    author="Test Author",
                    year=2024,
                    abstract="Test abstract",
                    category=category,
                    department=department,
                    course=course
                )
                self.stdout.write(f'Created test thesis: {thesis.title}')
            
            # Test co-author methods
            self.stdout.write(f'Thesis: {thesis.title}')
            self.stdout.write(f'Current co-authors: {thesis.get_coauthor_names()}')
            self.stdout.write(f'Co-author count: {thesis.co_authors.count()}')
            
            # Create test co-authors
            if thesis.co_authors.count() == 0:
                coauthor1 = CoAuthor.objects.create(
                    thesis=thesis,
                    first_name="John",
                    last_name="Doe",
                    student_id="12345",
                    email="john.doe@example.com"
                )
                coauthor2 = CoAuthor.objects.create(
                    thesis=thesis,
                    first_name="Jane",
                    last_name="Smith",
                    student_id="67890",
                    email="jane.smith@example.com"
                )
                self.stdout.write('Created test co-authors')
            
            # Test the methods again
            self.stdout.write(f'Co-authors after creation: {thesis.get_coauthor_names()}')
            self.stdout.write(f'Co-author details: {thesis.get_coauthor_details()}')
            
            self.stdout.write(
                self.style.SUCCESS('Co-author functionality test completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error testing co-authors: {str(e)}')
            )
