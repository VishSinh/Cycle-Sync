from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse

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
            
        print(ip_address)
        
        # Check if the client's IP address is rate limited and return an error if so   
        # key = f'rate_limit:{ip_address}'
        # count = cache.get(key)
        
        # if count is not None and count >= settings.RATE_LIMIT:
        #     return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
        
        # # Increment the count for the client's IP address and set the expiration time
        # if count is None:
        #     timeout_seconds = settings.RATE_LIMIT_WINDOW.total_seconds()
        #     cache.set(key, 1, timeout_seconds)
        # else:
        #     cache.incr(key)
            
        # cache.expire(key, settings.RATE_LIMIT_WINDOW.total_seconds())
        
        response = self.get_response(request)
        return response


