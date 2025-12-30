from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.management import call_command
from unittest.mock import patch
from .models import Plan, UserProfile
from datetime import timedelta

class SubscriptionCancellationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.plan = Plan.objects.create(name='Mecenas', level=2)
        self.profile = self.user.profile
        self.profile.current_plan = self.plan
        self.profile.stripe_subscription_id = 'sub_test_123'
        self.profile.subscription_end_date = timezone.now() + timedelta(days=30)
        self.profile.save()
        # Use force_login to bypass axes backend requirement
        self.client.force_login(self.user)

    @patch('stripe.Subscription.modify')
    def test_cancel_subscription(self, mock_stripe_modify):
        # Mock Stripe response
        mock_stripe_modify.return_value = {
            'id': 'sub_test_123',
            'cancel_at_period_end': True
        }

        response = self.client.post(reverse('cancel_subscription'))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

        # Check database update
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.cancel_at_period_end)
        
        # Check Stripe API call
        mock_stripe_modify.assert_called_once_with(
            'sub_test_123',
            cancel_at_period_end=True
        )

class SubscriptionExpirationTest(TestCase):
    def setUp(self):
        # Create user first, which triggers signal to create 'Livre' plan
        self.user = User.objects.create_user(username='expireduser', password='password')
        
        # Get the 'Livre' plan created by the signal
        self.free_plan = Plan.objects.get(name='Livre')
        
        self.paid_plan = Plan.objects.create(name='Mecenas', level=2)
        
        self.profile = self.user.profile
        self.profile.current_plan = self.paid_plan
        self.profile.stripe_subscription_id = 'sub_expired_456'
        # Set expiration date to yesterday
        self.profile.subscription_end_date = timezone.now() - timedelta(days=1)
        self.profile.save()

    def test_expiration_command(self):
        # Run the management command
        call_command('check_subscriptions')
        
        self.profile.refresh_from_db()
        
        # Check if plan was downgraded
        self.assertEqual(self.profile.current_plan, self.free_plan)
        
        # Check if subscription info was cleared/reset
        self.assertFalse(self.profile.cancel_at_period_end)

    def test_active_subscription_not_affected(self):
        # Create another user with active subscription
        active_user = User.objects.create_user(username='activeuser', password='password')
        active_profile = active_user.profile
        active_profile.current_plan = self.paid_plan
        active_profile.subscription_end_date = timezone.now() + timedelta(days=5)
        active_profile.save()

        call_command('check_subscriptions')
        
        active_profile.refresh_from_db()
        self.assertEqual(active_profile.current_plan, self.paid_plan)
