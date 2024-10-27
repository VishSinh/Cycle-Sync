from datetime import datetime, timedelta
from hashlib import sha256
from django_enumfield import enum
from rest_framework.views import APIView
from authentication.models import ActiveSessions
from jwt import encode as jwt_encode
from django.conf import settings

from users.models import User
from utils.exceptions import BadRequest
from utils.helpers import APIResponse, format_response
from utils.logger import logger
from authentication.serializers import AuthenticationSerializer
from authentication.helpers import create_hashed_value


class AutenticationView(APIView):
    authentication_serializer = AuthenticationSerializer
    
    class AuthType(enum.Enum):
        LOGIN = 1
        SIGNUP = 2 
    
    def generate_session_id(self, payload, expiry_time_minutes=settings.SESSION_EXPIRY):
        secret_key = settings.SESSION_SECRET_KEY 
        expiry_time = datetime.now() + timedelta(minutes=expiry_time_minutes)
        payload['exp'] = expiry_time
        token = jwt_encode(payload, secret_key, algorithm='HS256')
        
        return token
    
    @format_response
    def post(self, request):
        request_body = self.authentication_serializer(data=request.data)
        request_body.is_valid(raise_exception=True)

        auth_type = request_body.validated_data['auth_type']
        email = request_body.validated_data['email']
        password = request_body.validated_data['password']
        
        logger.info(f'Auth type: {auth_type} Email: {email} Password: {password}')
        
        password_hash = create_hashed_value(password)

        ########## LOGIN ##########
        if auth_type == self.AuthType.LOGIN:
            
            user = User.objects.filter(email=email, password=password_hash)
            if len(user) == 0:
                raise BadRequest('Invalid email or password')
            
            user = user[0]
            
            user_id_hash = user.user_id_hash
            
            active_session = ActiveSessions.objects.filter(user_id_hash=user_id_hash)
            if len(active_session) > 0:
                active_session.delete()
                
            session_id = self.generate_session_id(
                payload={'user_id_hash': user_id_hash}
            )
            
            active_session = ActiveSessions.objects.create(
                user_id_hash=user_id_hash, 
                session_id=session_id
            )
            
            response_body = {
                'message': 'Login successful',
                'user_id_hash': active_session.user_id_hash,
                'session_id': active_session.session_id,
            }
            
            return response_body

        ########## SIGNUP ##########
        user = User.objects.filter(email=email)
        if user:
            raise BadRequest('User already exists')
        
        user  = User.objects.create(email=email, password=password_hash)
        
        # Generate user_id_hash and save it
        user_id_hash = str(user.user_id) + settings.USER_ID_HASH_SALT
        user_id_hash = sha256(user_id_hash.encode('utf-8')).hexdigest()
        user.user_id_hash = user_id_hash
        user.save()

        # Generate session key
        session_id = self.generate_session_id(payload={'user_id_hash': user.user_id_hash})
        
        # Create active session
        active_session = ActiveSessions.objects.create(user_id_hash=user.user_id_hash, session_id=session_id)

        response_body = {
            'message': 'User created successfully',
            'user_id_hash': active_session.user_id_hash,
            'session_id': active_session.session_id,
        }
        return response_body, 201 


    
