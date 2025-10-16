from django.core.management.base import BaseCommand
from django.conf import settings
import json
import os
from main.utils import (
    optimize_search_parameters,
    get_optimized_search_parameters,
    set_optimized_search_parameters,
    get_optimization_statistics
)


class Command(BaseCommand):
    help = 'Run ABC optimization for search parameters and save results'

    def add_arguments(self, parser):
        parser.add_argument(
            '--iterations',
            type=int,
            default=100,
            help='Number of optimization iterations (default: 100)'
        )
        parser.add_argument(
            '--save-params',
            action='store_true',
            help='Save optimized parameters to file'
        )
        parser.add_argument(
            '--load-params',
            type=str,
            help='Load parameters from JSON file'
        )
        parser.add_argument(
            '--custom-queries',
            type=str,
            help='Path to JSON file with custom test queries'
        )
        parser.add_argument(
            '--colony-size',
            type=int,
            default=50,
            help='ABC colony size (default: 50)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('ABC Search Optimization Tool')
        )
        
        iterations = options['iterations']
        save_params = options['save_params']
        load_params_file = options['load_params']
        custom_queries_file = options['custom_queries']
        colony_size = options['colony_size']
        
        # Load custom queries if provided
        test_queries = None
        if custom_queries_file:
            try:
                with open(custom_queries_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    test_queries = data.get('queries', [])
                    self.stdout.write(f"Loaded {len(test_queries)} custom queries")
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error loading custom queries: {e}')
                )
                return
        
        # Load existing parameters if requested
        if load_params_file:
            try:
                with open(load_params_file, 'r', encoding='utf-8') as f:
                    params = json.load(f)
                    set_optimized_search_parameters(params)
                    self.stdout.write(
                        self.style.SUCCESS(f'Loaded parameters from {load_params_file}')
                    )
                    self._display_parameters(params)
                    return
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error loading parameters: {e}')
                )
                return
        
        # Run optimization
        self.stdout.write(f"Starting optimization with {iterations} iterations...")
        self.stdout.write(f"Colony size: {colony_size}")
        
        try:
            # Run optimization
            optimized_params = optimize_search_parameters(
                test_queries=test_queries,
                verbose=True
            )
            
            # Display results
            self.stdout.write(
                self.style.SUCCESS('\n=== OPTIMIZATION COMPLETED ===')
            )
            self._display_parameters(optimized_params)
            
            # Get optimization statistics
            stats = get_optimization_statistics()
            self.stdout.write(f"\nBest fitness: {stats.get('best_fitness', 0):.4f}")
            self.stdout.write(f"Total iterations: {stats.get('total_iterations', 0)}")
            
            # Save parameters if requested
            if save_params:
                params_file = os.path.join(settings.BASE_DIR, 'optimized_search_params.json')
                try:
                    with open(params_file, 'w', encoding='utf-8') as f:
                        json.dump(optimized_params, f, indent=2, ensure_ascii=False)
                    self.stdout.write(
                        self.style.SUCCESS(f'Parameters saved to {params_file}')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error saving parameters: {e}')
                    )
            
            # Show improvement if we have fitness history
            fitness_history = stats.get('fitness_history', [])
            if len(fitness_history) > 1:
                initial_fitness = fitness_history[0]
                final_fitness = fitness_history[-1]
                improvement = ((final_fitness - initial_fitness) / initial_fitness) * 100
                
                self.stdout.write(f"\n=== IMPROVEMENT ANALYSIS ===")
                self.stdout.write(f"Initial fitness: {initial_fitness:.4f}")
                self.stdout.write(f"Final fitness: {final_fitness:.4f}")
                self.stdout.write(f"Improvement: {improvement:.2f}%")
                
                # Find best iteration
                best_iteration = fitness_history.index(final_fitness)
                self.stdout.write(f"Best solution found at iteration: {best_iteration}")
            
            self.stdout.write(
                self.style.SUCCESS('\nOptimization completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during optimization: {str(e)}')
            )
            raise
    
    def _display_parameters(self, params):
        """Display optimized parameters in a formatted way."""
        self.stdout.write("\n=== OPTIMIZED PARAMETERS ===")
        
        # Group parameters by category
        weight_params = {k: v for k, v in params.items() if 'weight' in k}
        threshold_params = {k: v for k, v in params.items() if 'threshold' in k}
        other_params = {k: v for k, v in params.items() 
                       if 'weight' not in k and 'threshold' not in k}
        
        if weight_params:
            self.stdout.write("\nSearch Weights:")
            for param, value in sorted(weight_params.items()):
                self.stdout.write(f"  {param.replace('_weight', '').title()}: {value:.3f}")
        
        if threshold_params:
            self.stdout.write("\nThresholds:")
            for param, value in sorted(threshold_params.items()):
                self.stdout.write(f"  {param.replace('_threshold', '').title()}: {value:.3f}")
        
        if other_params:
            self.stdout.write("\nOther Parameters:")
            for param, value in sorted(other_params.items()):
                self.stdout.write(f"  {param.replace('_', ' ').title()}: {value:.3f}")
