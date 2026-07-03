from django.core.management.base import BaseCommand
from main.models import Thesis
from main.utils import extract_thesis_text

class Command(BaseCommand):
    help = 'Extracts and indexes full text for all existing theses'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-index even if full_text is already populated',
        )

    def handle(self, *args, **options):
        force = options['force']
        if force:
            theses = Thesis.objects.all()
        else:
            theses = Thesis.objects.filter(full_text__isnull=True) | Thesis.objects.filter(full_text='')
        
        total = theses.count()
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS('All theses are already indexed.'))
            return

        self.stdout.write(f'Starting re-indexing for {total} theses...')
        
        count = 0
        for thesis in theses:
            if not thesis.file:
                continue
            
            try:
                self.stdout.write(f'Indexing [{count+1}/{total}]: {thesis.title}')
                text = extract_thesis_text(thesis)
                if text:
                    thesis.full_text = text
                    thesis.save(update_fields=['full_text'])
                    count += 1
                else:
                    self.stdout.write(self.style.WARNING(f'Could not extract text from: {thesis.title}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error indexing {thesis.title}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully indexed {count} theses.'))
