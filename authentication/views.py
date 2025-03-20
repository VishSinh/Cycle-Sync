import logging
from datetime import datetime, timedelta
from hashlib import sha256
from django_enumfield import enum
from rest_framework.views import APIView
from jwt import encode as jwt_encode
from django.conf import settings

from users.models import User, UserDetails
from utils.exceptions import  Conflict, ResourceNotFound, Unauthorized
from utils.helpers import forge
from authentication.serializers import AuthenticationSerializer
from authentication.helpers import create_hashed_value

logger = logging.getLogger(__name__)


class AutenticationView(APIView):
    
    class AuthType(enum.Enum):
        LOGIN = 1
        SIGNUP = 2 
    
    def generate_token(self, payload, expiry_time_minutes=settings.SESSION_EXPIRY):
        secret_key = settings.SESSION_SECRET_KEY 
        expiry_time = datetime.now() + timedelta(minutes=expiry_time_minutes)
        payload['exp'] = expiry_time
        token = jwt_encode(payload, secret_key, algorithm='HS256')
        
        return token
    
    @forge
    def post(self, request):
        serializer = AuthenticationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        auth_type = serializer.get_value('auth_type')
        email = serializer.get_value('email')
        password = serializer.get_value('password')
        
        password_hash = create_hashed_value(password)

        ########## LOGIN ##########
        if auth_type == self.AuthType.LOGIN:
            
            user = User.objects.filter(email=email, password=password_hash)
            if len(user) == 0:
                raise Unauthorized('Invalid email or password')
            
            user = user[0]
            
            user_id_hash = user.user_id_hash
                
            token = self.generate_token(payload={'user_id_hash': user_id_hash})
            
            logger.info(f'User {user_id_hash} logged in successfully')
            
            user_details_exists = UserDetails.objects.filter(user_id_hash=user_id_hash)
            
            user_details_exists = len(user_details_exists) > 0
            
            logger.info(f'User details exists: {user_details_exists}')
            
            response_body = {
                'message': 'Login successful',
                'token': token,
                'exists': user_details_exists
            }
            
            return response_body

        ########## SIGNUP ##########
        user = User.objects.filter(email=email)
        if user:
            raise Conflict('User already exists')
        
        user  = User.objects.create(email=email, password=password_hash)
        
        # Generate user_id_hash and save it
        user_id_hash = str(user.user_id) + settings.USER_ID_HASH_SALT
        user_id_hash = sha256(user_id_hash.encode('utf-8')).hexdigest()
        user.user_id_hash = user_id_hash
        user.save()

        # Generate session key
        token = self.generate_token(payload={'user_id_hash': user.user_id_hash})
        

        response_body = {
            'message': 'User created successfully',
            'token': token,
            'exists': False
        }
        
        return response_body, 201 


    
class PingView(APIView):
    
    @forge
    def get(self, request):
        logger.info('Ping')
        logger.info(request.user_obj.__dict__)
        return {'message': 'Pong'}