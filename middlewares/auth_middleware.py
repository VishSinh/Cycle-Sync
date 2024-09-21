from authentication.models import ActiveSessions
from utils.exceptions import Unauthorized

from django.conf import settings
from datetime import datetime, timedelta
from rest_framework import status
from utils.helpers import APIResponse


class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.skip_auth_patterns = getattr(settings, 'SKIP_AUTH_PATTERNS', [])

    def __call__(self, request):
        if any(request.path.startswith(pattern) for pattern in self.skip_auth_patterns):
            return self.get_response(request)

        try:
            if "Authorization" not in request.headers or "user_id_hash" not in request.data:
                raise Unauthorized('Authentication credentials were not provided')
            
            active_session = ActiveSessions.objects.filter(
                user_id_hash=request.data["user_id_hash"], 
                session_id=request.headers['Authorization'].split(' ')[1])

            if len(active_session) == 0:
                raise Unauthorized('Invalid Authorization credentials')
            
            if active_session[0].created_at < datetime.now() - timedelta(minutes=settings.SESSION_EXPIRY):
                active_session.delete()
                raise Unauthorized('Session expired')

            return self.get_response(request)
        except Unauthorized as e:
            return APIResponse(success=False, status_code=status.HTTP_401_UNAUTHORIZED, error=e).response()
        except Exception as e:
            raise APIResponse(success=False, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error=e).response()

    