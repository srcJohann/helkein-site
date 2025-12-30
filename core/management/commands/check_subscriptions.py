from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import UserProfile, Plan
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check for expired subscriptions and downgrade users to Free plan'

    def handle(self, *args, **options):
        now = timezone.now()
        expired_profiles = UserProfile.objects.filter(
            subscription_end_date__lt=now,
            current_plan__level__gt=0  # Only check paid plans
        )

        count = 0
        for profile in expired_profiles:
            # Downgrade to Free plan (assuming ID 1 or name 'Livre' is free)
            # Ideally, fetch the default free plan
            free_plan = Plan.objects.filter(level=0).first()
            if not free_plan:
                free_plan = Plan.objects.filter(name='Livre').first()
            
            if free_plan:
                old_plan = profile.current_plan.name
                profile.current_plan = free_plan
                profile.stripe_subscription_id = None
                profile.subscription_end_date = None
                profile.cancel_at_period_end = False
                profile.save()
                
                self.stdout.write(self.style.SUCCESS(f'Downgraded user {profile.user.username} from {old_plan} to {free_plan.name}'))
                count += 1
            else:
                self.stdout.write(self.style.ERROR(f'Free plan not found. Could not downgrade user {profile.user.username}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully checked subscriptions. Downgraded {count} users.'))
