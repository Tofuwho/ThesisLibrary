from django.core.management.base import BaseCommand
from main.utils import (
    get_performance_report,
    save_performance_stats,
    load_performance_stats,
    reset_performance_stats
)
import json


class Command(BaseCommand):
    help = 'Manage and view search performance statistics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--show',
            action='store_true',
            help='Show current performance statistics'
        )
        parser.add_argument(
            '--save',
            type=str,
            help='Save statistics to specified file'
        )
        parser.add_argument(
            '--load',
            type=str,
            help='Load statistics from specified file'
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all performance statistics'
        )
        parser.add_argument(
            '--format',
            choices=['json', 'table'],
            default='table',
            help='Output format (default: table)'
        )

    def handle(self, *args, **options):
        if options['reset']:
            reset_performance_stats()
            self.stdout.write(
                self.style.SUCCESS('Performance statistics reset successfully!')
            )
            return

        if options['load']:
            try:
                load_performance_stats(options['load'])
                self.stdout.write(
                    self.style.SUCCESS(f'Statistics loaded from {options["load"]}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error loading statistics: {e}')
                )
                return

        if options['save']:
            try:
                save_performance_stats(options['save'])
                self.stdout.write(
                    self.style.SUCCESS(f'Statistics saved to {options["save"]}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error saving statistics: {e}')
                )
                return

        if options['show'] or not any([options['save'], options['load'], options['reset']]):
            try:
                report = get_performance_report()
                
                if options['format'] == 'json':
                    self.stdout.write(json.dumps(report, indent=2))
                else:
                    self._display_table_report(report)
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error retrieving statistics: {e}')
                )

    def _display_table_report(self, report):
        """Display performance report in table format."""
        self.stdout.write(
            self.style.SUCCESS('\n=== SEARCH PERFORMANCE REPORT ===')
        )
        
        # Search Statistics
        search_stats = report.get('search_stats', {})
        self.stdout.write(f"\n📊 Search Statistics:")
        self.stdout.write(f"  Total searches: {search_stats.get('total_searches', 0)}")
        self.stdout.write(f"  Optimized searches: {search_stats.get('optimized_searches', 0)}")
        self.stdout.write(f"  Average response time: {search_stats.get('average_response_time', 0):.3f}s")
        
        optimization_ratio = report.get('optimization_ratio', 0)
        self.stdout.write(f"  Optimization usage: {optimization_ratio:.1%}")
        
        # Optimization Statistics
        opt_stats = report.get('optimization_stats', {})
        self.stdout.write(f"\n🔧 Optimization Statistics:")
        self.stdout.write(f"  Total optimizations: {opt_stats.get('total_optimizations', 0)}")
        self.stdout.write(f"  Best fitness achieved: {opt_stats.get('best_fitness_achieved', 0):.4f}")
        
        avg_opt_time = opt_stats.get('average_optimization_time', 0)
        if avg_opt_time > 0:
            self.stdout.write(f"  Average optimization time: {avg_opt_time:.2f}s")
        
        last_opt_time = opt_stats.get('last_optimization_time')
        if last_opt_time:
            import datetime
            last_opt_dt = datetime.datetime.fromtimestamp(last_opt_time)
            self.stdout.write(f"  Last optimization: {last_opt_dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Top Queries
        top_queries = report.get('top_queries', [])
        if top_queries:
            self.stdout.write(f"\n🔍 Top Queries:")
            for i, query_info in enumerate(top_queries[:10], 1):
                query = query_info.get('query', '')
                count = query_info.get('count', 0)
                self.stdout.write(f"  {i:2d}. {query:<30} ({count} searches)")
        
        # Recent Performance
        recent_perf = report.get('recent_performance', [])
        if recent_perf:
            self.stdout.write(f"\n⏱️  Recent Performance (last {len(recent_perf)} searches):")
            
            avg_recent_time = sum(p.get('response_time', 0) for p in recent_perf) / len(recent_perf)
            optimized_count = sum(1 for p in recent_perf if p.get('optimized', False))
            
            self.stdout.write(f"  Average response time: {avg_recent_time:.3f}s")
            self.stdout.write(f"  Optimized searches: {optimized_count}/{len(recent_perf)}")
            
            # Show last few searches
            self.stdout.write(f"  Recent searches:")
            for perf in recent_perf[-5:]:
                opt_indicator = "✓" if perf.get('optimized', False) else "○"
                response_time = perf.get('response_time', 0)
                self.stdout.write(f"    {opt_indicator} {response_time:.3f}s")
        
        self.stdout.write("\n" + "="*50)
