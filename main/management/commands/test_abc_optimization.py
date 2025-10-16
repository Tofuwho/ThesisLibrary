from django.core.management.base import BaseCommand
from main.utils import (
    optimize_search_parameters, 
    get_optimized_search_parameters,
    get_optimization_statistics,
    batch_optimize_search,
    enhanced_search_in_thesis_pdf
)
from main.models import Thesis


class Command(BaseCommand):
    help = 'Test ABC optimization for search parameters'

    def add_arguments(self, parser):
        parser.add_argument(
            '--iterations',
            type=int,
            default=50,
            help='Number of optimization iterations (default: 50)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
        parser.add_argument(
            '--test-queries',
            nargs='+',
            default=[
                "SRE"
            ],
            help='Test queries for optimization'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting ABC optimization for search parameters...')
        )
        
        iterations = options['iterations']
        verbose = options['verbose']
        test_queries = options['test_queries']
        
        # Run optimization
        self.stdout.write(f"Running optimization with {iterations} iterations...")
        self.stdout.write(f"Test queries: {', '.join(test_queries)}")
        
        try:
            # Run batch optimization
            results = batch_optimize_search(
                queries=test_queries,
                max_iterations=iterations,
                verbose=verbose
            )
            
            # Display results
            self.stdout.write(
                self.style.SUCCESS('\n=== OPTIMIZATION RESULTS ===')
            )
            
            self.stdout.write(f"Best fitness achieved: {results['best_fitness']:.4f}")
            self.stdout.write(f"Total iterations: {results['total_iterations']}")
            
            self.stdout.write('\n=== OPTIMIZED PARAMETERS ===')
            for param, value in results['optimized_parameters'].items():
                self.stdout.write(f"{param}: {value:.3f}")
            
            # Show fitness improvement over time
            fitness_history = results['fitness_history']
            if len(fitness_history) > 1:
                initial_fitness = fitness_history[0]
                final_fitness = fitness_history[-1]
                improvement = ((final_fitness - initial_fitness) / initial_fitness) * 100
                
                self.stdout.write(f"\n=== IMPROVEMENT SUMMARY ===")
                self.stdout.write(f"Initial fitness: {initial_fitness:.4f}")
                self.stdout.write(f"Final fitness: {final_fitness:.4f}")
                self.stdout.write(f"Improvement: {improvement:.2f}%")
            
            # Test enhanced search if theses are available
            self.stdout.write(f"\n=== TESTING ENHANCED SEARCH ===")
            theses = Thesis.objects.filter(file__isnull=False)[:3]  # Get first 3 theses with files
            
            if theses:
                test_query = test_queries[0] if test_queries else "machine learning"
                self.stdout.write(f"Testing search with query: '{test_query}'")
                
                for thesis in theses:
                    self.stdout.write(f"\nTesting thesis: {thesis.title}")
                    try:
                        # Test enhanced search
                        results = enhanced_search_in_thesis_pdf(thesis, test_query)
                        
                        if results.get('found'):
                            matches_count = results.get('total_matches', 0)
                            self.stdout.write(f"  ✓ Found {matches_count} matches")
                            
                            # Show optimization metadata if available
                            if results.get('optimization_used'):
                                fuzzy_threshold = results.get('fuzzy_threshold', 'N/A')
                                context_window = results.get('context_window', 'N/A')
                                self.stdout.write(f"  ✓ Optimization applied (fuzzy: {fuzzy_threshold}, context: {context_window})")
                        else:
                            self.stdout.write(f"  ✗ No matches found")
                            
                    except Exception as e:
                        self.stdout.write(f"  ✗ Error: {str(e)}")
            else:
                self.stdout.write("No theses with files found for testing")
            
            self.stdout.write(
                self.style.SUCCESS('\nABC optimization test completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during optimization: {str(e)}')
            )
            raise
