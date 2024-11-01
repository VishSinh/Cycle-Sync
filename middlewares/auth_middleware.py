from authentication.models import ActiveSessions
from utils.logger import logger
from utils.exceptions import Unauthorized
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
from rest_framework import status
from utils.helpers import APIResponse


from utils.exceptions import Unauthorized
from django.conf import settings
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.skip_auth_patterns = getattr(settings, 'SKIP_AUTH_PATTERNS', [])

    def decode_token(self, token):
        try:
            payload = jwt.decode(token, settings.SESSION_SECRET_KEY,algorithms=['HS256'])
            return payload
        except ExpiredSignatureError:
            raise Unauthorized('Session expired')
        except InvalidTokenError:
            raise Unauthorized('Invalid token')

    def extract_token(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header:
            raise Unauthorized('Authentication credentials were not provided')
        
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            raise Unauthorized('Invalid authorization header format')
        
        return parts[1]

    def __call__(self, request):
        if any(request.path.startswith(pattern) for pattern in self.skip_auth_patterns):
            return self.get_response(request)

        try:
            token = self.extract_token(request)
            payload = self.decode_token(token)
            
            user_id_hash = payload.get('user_id_hash')
            if not user_id_hash:
                raise Unauthorized('Invalid token payload')
            
            request.user_id_hash = user_id_hash
            
            active_session = ActiveSessions.objects.filter(
                user_id_hash=user_id_hash,
                session_id=token
            ).first()
            
            if not active_session:
                raise Unauthorized('Invalid Authorization credentials')
            
            if active_session.created_at < timezone.now() - timedelta(minutes=settings.SESSION_EXPIRY):
                active_session.delete()
                raise Unauthorized('Session expired')
            return self.get_response(request)
            
        except Unauthorized as e:
            return APIResponse(success=False, status_code=status.HTTP_401_UNAUTHORIZED, error=str(e)).response()
        except Exception as e:
            print(f'Exception: {e}')
            return APIResponse(success=False, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error=str(e)).response()

    