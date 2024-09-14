from datetime import datetime, timedelta
from traceback import print_exc
from typing import Any, Dict, Optional
from django.conf import settings
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
from functools import wraps
import logging

from authentication.models import ActiveSessions

logger = logging.getLogger(__name__)


'''
---DECORATOR---
Used to validate the token in the request headers
'''
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
            
            if active_session[0].created_at < datetime.now() - timedelta(minutes=settings.SESSION_EXPIRY):
                return response_obj(success=False, message='Session expired', status_code=status.HTTP_401_UNAUTHORIZED)
        
            return func(request, *args, **kwargs)
        
        except Exception as e:
            print_exc(e)
            return response_obj(success=False, message='An error occured', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    return wrapper_func 

       
def response_obj(success=True, message='', status_code=200, data={}, error=''):
    if(not error == ''):
        print_exc(error)
        
    data = {
        "success": success,
        "message": message,
        "data": data
    }
    return Response(data, status=status_code)


'''
Get the value of a key from a serializer's validated data
Used to ensure that we get a default value if the key is not present in the validated data
''' 
def get_serialized_data(serializer, key, default=''):
    if key in serializer.validated_data:
        return serializer.validated_data[key]
    return default


'''
---DECORATOR---
When wrapped on a function in a view, one can simply return a dictionary or a tuple of dictionary and status code
'''
def format_response(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            if isinstance(result, tuple) and len(result) == 2:
                response_body, status_code = result
                return APIResponse(data=response_body, status_code=status_code).response()
            
            return APIResponse(data=result).response()
        
        except Exception as e:
            return APIResponse(success=False, status_code=500, error=e).response()
    
    return wrapper


'''
Custom Response Class to format the response in a consistent manner
'''
class APIResponse:
    def __init__(self, success: bool = True, status_code: int = 200, 
                    data: Optional[Dict[str, Any]] = None, error: Optional[Exception] = None):
        self.success = success
        self.status_code = status_code
        self.data = data or {}
        self.error = error

    def response(self, correlation_id: Optional[str] = None) -> JsonResponse: 
        if self.error:
            logger.error(f"Error occurred: {str(self.error)}", exc_info=True, extra={'correlation_id': correlation_id})
        
        response_data: Dict[str, Any] = {
            "success": self.success,
            "data": self.data
        }

        if self.error:
            response_data["error"] = {
                "code": self.error.__class__.__name__,
                "message": str(self.error.message) if hasattr(self.error, "message") else 'An error occurred',
                "details": str(self.error.details) if hasattr(self.error, "details") else str(self.error)
            }
        else :
            response_data["error"] = {
                "code": "",
                "message": "",
                "details": ""
            }

        if correlation_id:
            response_data["correlation_id"] = correlation_id


        return JsonResponse(response_data, status=self.status_code)

    def __str__(self) -> str:
        return f"APIResponse(success={self.success}, status_code={self.status_code}, data={self.data}, error={self.error})"
