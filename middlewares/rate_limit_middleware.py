from datetime import timedelta, timezone
from django.conf import settings
from authentication.models import TrackerRegisteredUserRequests, TrackerNonRegisteredUserRequests
from utils.exceptions import TooManyRequests
from utils.helpers import APIResponse
from rest_framework import status
from django.conf import settings
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied as DjangoPermissionDenied
from django.http import HttpRequest, HttpResponse



# Set up logging for this module

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        ip_address = self.get_client_ip(request)
        user_id_hash = request.GET.get('user_id_hash')

        if user_id_hash:
            self.process_user_requests(user_id_hash, ip_address)
        else:
            self.process_non_registered_user_request(ip_address)

        return self.get_response(request)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
    
    def process_non_registered_user_request(self, ip_address):
        tracker_request, created = TrackerNonRegisteredUserRequests.objects.get_or_create(ip_address=ip_address)
        tracker_request.count += 1
        tracker_request.save()

        if tracker_request.count > settings.NON_REGISTERED_RATE_LIMIT:
            return self.rate_limit_exceeded_response()
    
    def process_user_requests(self, user_id_hash, ip_address):
        tracker_request, created = TrackerRegisteredUserRequests.objects.get_or_create(
            user_id_hash=user_id_hash,
            defaults={'ip_address': ip_address}
        )
        tracker_request.count += 1
        
        # Check if the user has made a request within the last REGISTERED_FREQ_RATE_LIMIT_MINUTES minutes
        if tracker_request.freq_req_at and tracker_request.freq_req_at > timezone.now() - timedelta(minutes=settings.REGISTERED_FREQ_RATE_LIMIT_MINUTES):
            tracker_request.freq_count += 1
        else:
            tracker_request.freq_count = 1
            tracker_request.freq_req_at = timezone.now()

        tracker_request.save()

        if tracker_request.count > settings.REGISTERED_RATE_LIMIT or tracker_request.freq_count > settings.REGISTERED_FREQ_RATE_LIMIT:
            return self.rate_limit_exceeded_response()

    def rate_limit_exceeded_response(self):
        return APIResponse(success=False, status_code=status.HTTP_429_TOO_MANY_REQUESTS, error=TooManyRequests('Rate limit exceeded')).response()
