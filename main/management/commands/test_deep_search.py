from django.core.management.base import BaseCommand
from main.models import Thesis
from main.utils import search_in_thesis_pdf, extract_thesis_text

class Command(BaseCommand):
    help = 'Test deep search functionality'

    def handle(self, *args, **options):
        self.stdout.write('Testing deep search functionality...')
        
        try:
            # Get the first thesis with a file
            thesis = Thesis.objects.filter(file__isnull=False).first()
            
            if not thesis:
                self.stdout.write('No thesis with PDF file found.')
                return
            
            self.stdout.write(f'Testing with thesis: {thesis.title}')
            self.stdout.write(f'PDF file: {thesis.file.name}')
            
            # Test text extraction
            self.stdout.write('\n--- Testing Text Extraction ---')
            text_content = extract_thesis_text(thesis)
            if text_content:
                self.stdout.write(f'Extracted text length: {len(text_content)} characters')
                self.stdout.write(f'First 200 characters: {text_content[:200]}...')
            else:
                self.stdout.write('No text extracted from PDF')
            
            # Test deep search with common terms
            test_queries = ['thesis', 'research', 'methodology', 'conclusion', 'abstract']
            
            for query in test_queries:
                self.stdout.write(f'\n--- Testing search for: "{query}" ---')
                results = search_in_thesis_pdf(thesis, query)
                
                if results.get('found'):
                    self.stdout.write(f'✓ Found {results["total_matches"]} matches')
                    if results.get('context'):
                        self.stdout.write(f'Context: {results["context"][:200]}...')
                else:
                    self.stdout.write('✗ No matches found')
            
            self.stdout.write(
                self.style.SUCCESS('\nDeep search functionality test completed!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error testing deep search: {str(e)}')
            )
