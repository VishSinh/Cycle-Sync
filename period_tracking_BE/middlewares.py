from datetime import timedelta, timezone
from django.conf import settings
from authentication.models import TrackerRegisteredUserRequests, TrackerNonRegisteredUserRequests
from period_tracking_BE.helpers.utils import response_obj
from rest_framework import status

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        
        # Get the client's IP address
        ip_address = ''
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
                        
        user_id_hash = request.GET.get('user_id_hash')

        if user_id_hash:
            self.process_user_requests(user_id_hash, ip_address)
        else:
            tracker_requests, created = TrackerNonRegisteredUserRequests.objects.get_or_create(ip_address=ip_address)
            tracker_requests.count += 1
            tracker_requests.save()

            if tracker_requests.count > settings.NON_REGISTERED_RATE_LIMIT:
                return response_obj(success=False, message='Rate limit exceeded', status_code=status.HTTP_429_TOO_MANY_REQUESTS)

        return self.get_response(request)
    
    
    def process_user_requests(self, user_id_hash, ip_address):
        tracker_request, created = TrackerRegisteredUserRequests.objects.get_or_create(
            user_id_hash=user_id_hash,
            defaults={'ip_address': ip_address}
        )
        # Update daily request count
        tracker_request.count += 1

        # Update the frequent request count
        if tracker_request.freq_req_at and tracker_request.freq_req_at > timezone.now() - timedelta(minutes=settings.REGISTERED_FREQ_RATE_LIMIT_MINUTES):
            tracker_request.freq_count += 1
        else:
            tracker_request.freq_count = 1
            tracker_request.freq_req_at = timezone.now()

        tracker_request.save()

        if tracker_request.count > settings.REGISTERED_RATE_LIMIT or tracker_request.freq_count > settings.REGISTERED_FREQ_RATE_LIMIT:
            return response_obj(success=False, message='Rate limit exceeded', status_code=status.HTTP_429_TOO_MANY_REQUESTS)
        
        



