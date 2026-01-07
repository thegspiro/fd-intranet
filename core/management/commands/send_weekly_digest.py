"""
Management command to send weekly audit digest
Can be run manually or via scheduled task
"""
from django.core.management.base import BaseCommand
from core.weekly_digest import WeeklyDigestService
from django.utils import timezone


class Command(BaseCommand):
    help = 'Generate and send weekly audit digest to IT Director'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Test mode - shows what would be sent without actually sending'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Generating weekly audit digest...'))
        
        try:
            result = WeeklyDigestService.generate_and_send_digest()
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n✓ Weekly digest sent successfully!\n"
                        f"  Recipients: {', '.join(result['recipients'])}\n"
                        f"  Date Range: {result['date_range']}\n"
                        f"  Country Changes: {result['country_changes']}\n"
                        f"  Security Events: {result['security_events']}\n"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"\n✗ Failed to send digest\n"
                        f"  Error: {result.get('error', 'Unknown error')}\n"
                    )
                )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"\n✗ Error: {str(e)}\n")
            )
            raise
