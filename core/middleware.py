from django.utils import timezone
from .models import DailyVisit

class DailyVisitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Logic to count daily visits
        # We use session to avoid counting the same user multiple times a day
        today = timezone.now().date().isoformat()
        
        if not request.session.get(f'visited_{today}'):
            try:
                visit, created = DailyVisit.objects.get_or_create(date=timezone.now().date())
                # If it's not created, we still increment because this is a new session/user for today
                # Wait, get_or_create returns the object.
                # If we want to count unique visitors, we should only increment if session doesn't have the flag.
                # But DailyVisit.count is a simple integer.
                # We need to handle concurrency properly, using F() expression.
                from django.db.models import F
                
                if created:
                    # If created, count is 0 (default), so we set to 1.
                    visit.count = 1
                    visit.save()
                else:
                    visit.count = F('count') + 1
                    visit.save()
                
                request.session[f'visited_{today}'] = True
            except Exception:
                # Ignore errors to not break the site
                pass

        response = self.get_response(request)
        return response
