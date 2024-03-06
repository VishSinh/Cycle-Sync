from functools import wraps
from hashlib import sha256
from traceback import print_exc
from django.forms import model_to_dict
from rest_framework.response import Response
from rest_framework import status

from authentication.models import ActiveSessions

def validate_token(func):
    
    def wrapper_func(request, *args, **kwargs):
        try:
            if "Authorization" not in request.headers or "user_id_hash" not in request.data:
                return response_obj(success=False, message='Auth Credentials not found in request', status_code=status.HTTP_401_UNAUTHORIZED)
            
            active_session = ActiveSessions.objects.filter(
                user_id_hash=request.data["user_id_hash"], 
                session_id=request.headers['Authorization'].split(' ')[1])

            if len(active_session) == 0:
                return response_obj(success=False, message='Invalid Auth Credentials', status_code=status.HTTP_401_UNAUTHORIZED)
        
            return func(request, *args, **kwargs)
        
        except Exception as e:
            print_exc(e)
            return response_obj(success=False, message='An error occured', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    return wrapper_func
            
        
def response_obj(success=True, message='', status_code=200, data={}):
    data = {
        "success": success,
        "message": message,
        "data": data
    }
    return Response(data, status=status_code)

def create_hashed_value(value):
        value_bytes = value.encode('utf-8')
        hash_object = sha256()
        hash_object.update(value_bytes)
        hashed_value = hash_object.hexdigest()

        return hashed_value
    
def get_serialized_data(serializer, key, default=''):
    if key in serializer.validated_data:
        return serializer.validated_data[key]
    return default
    

