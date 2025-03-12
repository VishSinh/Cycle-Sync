import jwt
from django.conf import settings
from datetime import UTC, datetime
from rest_framework import status

from users.models import User
from utils.exceptions import InternalServerError, Unauthorized
from utils.helpers import APIResponse
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.skip_auth_patterns = getattr(settings, 'SKIP_AUTH_PATTERNS', [])

    def verify_token(self, token: str):
        try:
            decoded_token = jwt.decode(token, settings.SESSION_SECRET_KEY, algorithms=['HS256'])
            logger.info(f"Decoded token: {decoded_token}")
            token_uuid = decoded_token.get('user_id_hash')
            expiry = datetime.fromtimestamp(decoded_token.get('exp'), tz=UTC)
            
            if expiry < datetime.now(UTC):
                raise Unauthorized('Token expired')
            
            return token_uuid, expiry
        except jwt.ExpiredSignatureError:
            raise Unauthorized('Token expired')
        except jwt.InvalidTokenError:
            raise Unauthorized('Invalid Token')
        except Exception as e:
            raise InternalServerError('Error verifying token')

    def __call__(self, request):
        try:
            if any(pattern in request.path for pattern in self.skip_auth_patterns):
                return self.get_response(request)
            
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                raise Unauthorized('Authentication credentials were not provided')
            
            token = auth_header.split(' ')[1]
            user_id_hash, expiry = self.verify_token(token)
            
            user = User.objects.filter(user_id_hash=user_id_hash).first()
            if not user:
                raise Unauthorized('Invalid user')
            
            request.user_obj = user
            logger.info(f"Incoming request from user: {request.user_obj.email}")
            
            return self.get_response(request)
        except Unauthorized as e:
            return APIResponse(success=False, status_code=status.HTTP_401_UNAUTHORIZED, error=str(e)).response()
        except Exception as e:
            # logger.error(f'Exception: {e}')
            return APIResponse(success=False, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, error=str(e)).response()
            