from datetime import datetime, timedelta
from hashlib import sha256
from django.forms import model_to_dict
from django_enumfield import enum
from rest_framework.views import APIView
from rest_framework import status
from authentication.models import ActiveSessions
from jwt import encode as jwt_encode

from users.models import User
from period_tracking_BE.helpers.exceptions import CustomException
from period_tracking_BE.helpers.utils import create_hashed_value, response_obj
from authentication.serializers import AuthenticationSerializer


class AutenticationView(APIView):
    authentication_serializer = AuthenticationSerializer
    
    class AuthType(enum.Enum):
        LOGIN = 1
        SIGNUP = 2 
    
    def generate_session_id(self, payload, expiry_time_minutes=60):
        secret_key = 'd8f7a8s7ana0191hJAIFBUuf9y1b' #TODO: This and default expiry_time_minutes should be stored in environment variable
        expiry_time = datetime.utcnow() + timedelta(minutes=expiry_time_minutes)
        payload['exp'] = expiry_time
        token = jwt_encode(payload, secret_key, algorithm='HS256')
        
        return token
    
    def post(self, request):
        try:
            request_body = self.authentication_serializer(data=request.data)
            
            ########## HANDLE VALIDATION ERROR ##########
            if not request_body.is_valid():
                errors = request_body.errors
                message = "; ".join([errors[key][0] if key == "non_field_errors" else f"{key} - {errors[key][0]}" for key in errors])
                return response_obj(success=False, message=message, status_code=status.HTTP_400_BAD_REQUEST)
            #############################################

            auth_type = request_body.validated_data['auth_type']
            email = request_body.validated_data['email']
            password = request_body.validated_data['password']
            
            password_hash = create_hashed_value(password)
    
            ########## LOGIN ##########
            if auth_type == self.AuthType.LOGIN:
                
                user = User.objects.filter(email=email, password=password_hash)
                if len(user) == 0:
                    raise CustomException('Invalid email or password')
                
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
                    'user_id_hash': active_session.user_id_hash,
                    'session_id': active_session.session_id
                }
                return response_obj(message='Logged in successfully',data=response_body)
            
            ########## SIGNUP ##########
            user = User.objects.filter(email=email)
            if user:
                raise CustomException('User already exists')
            
            user  = User.objects.create(email=email, password=password_hash)
            
            # Generate user_id_hash and save it
            user_id_hash = str(user.user_id) + 'A#DSfe85bc3c5d9fbcafaf5fc80db7b0e9b67DSjidjhW'
            user_id_hash = sha256(user_id_hash.encode('utf-8')).hexdigest()
            user.user_id_hash = user_id_hash
            user.save()

            # Generate session key
            session_id = self.generate_session_id(payload={'user_id_hash': user.user_id_hash})
            
            # Create active session
            active_session = ActiveSessions.objects.create(user_id_hash=user.user_id_hash, session_id=session_id)

            response_body = {
                'user_id_hash': active_session.user_id_hash,
                'session_id': active_session.session_id
            }
            return response_obj(message='Signed up successfully',data=response_body)
  
        except CustomException as e:
            return response_obj(success=False, message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)   
            
        except Exception as e:
            print(e)
            return response_obj(success=False, message='An error occured', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)