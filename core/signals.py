from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile, Plan

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        plan, _ = Plan.objects.get_or_create(name="Livre", defaults={'level': 0})
        UserProfile.objects.create(user=instance, current_plan=plan)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()