# from datetime import datetime, timedelta
import json
from traceback import print_exc
from typing import Any, Dict, Optional
from django.conf import settings
from django.http import JsonResponse
from django.db import models
from django.utils import timezone
import pytz
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from functools import wraps

from utils.exceptions import BadRequest

IST = pytz.timezone("Asia/Kolkata")  


'''
---DECORATOR---
Used to validate the token in the request headers
'''
# def validate_token(func):
    
#     def wrapper_func(request, *args, **kwargs):
#         try:
#             if "Authorization" not in request.headers or "user_id_hash" not in request.data:
#                 return response_obj(success=False, message='Auth Credentials not found in request', status_code=status.HTTP_401_UNAUTHORIZED)
            
#             active_session = ActiveSessions.objects.filter(
#                 user_id_hash=request.data["user_id_hash"], 
#                 session_id=request.headers['Authorization'].split(' ')[1])

#             if len(active_session) == 0:
#                 return response_obj(success=False, message='Invalid Auth Credentials', status_code=status.HTTP_401_UNAUTHORIZED)
            
#             if active_session[0].created_at < datetime.now() - timedelta(minutes=settings.SESSION_EXPIRY):
#                 return response_obj(success=False, message='Session expired', status_code=status.HTTP_401_UNAUTHORIZED)
        
#             return func(request, *args, **kwargs)
        
#         except Exception as e:
#             print_exc(e)
#             return response_obj(success=False, message='An error occured', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
#     return wrapper_func 

       
# def response_obj(success=True, message='', status_code=200, data={}, error=''):
#     if(not error == ''):
#         print_exc(error)
        
#     data = {
#         "success": success,
#         "message": message,
#         "data": data
#     }
#     return Response(data, status=status_code)


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
def forge(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
            
        if isinstance(result, Exception):
            raise result
        try:
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
    def __init__(self, success: bool = True, status_code: int = 200, data: Optional[Any] = None, error: Optional[Exception] = None):
        self.success = success
        self.status_code = status_code
        self.data = data if data is not None else {}
        self.error = error

    def _format_error(self) -> Dict[str, str]:
        if not self.error:
            return {"code": "", "message": "", "details": ""}
        
        return {"code": self.error.__class__.__name__, "message": getattr(self.error, "message", "An error occurred"), "details": getattr(self.error, "details", str(self.error))}

    def response(self, correlation_id: Optional[str] = None) -> JsonResponse:
        response_data = {"success": self.success, "data": self.data, "error": self._format_error()}

        if correlation_id:
            response_data["correlation_id"] = correlation_id

        return JsonResponse(response_data, status=self.status_code)

    def __str__(self) -> str: 
        return f"APIResponse(success={self.success}, status_code={self.status_code}, data={self.data}, error={self.error})"



'''
Custom Serializer class to inherit from to handle validation errors
'''
class BaseSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        """
        Override to_internal_value to provide custom error formatting.
        Converts validation errors to a flat list of error messages.
        """
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as exc:
            error_messages = [
                f"{key} - {error}" if key != "non_field_errors" else error
                for key, errors in exc.detail.items()
                for error in errors
            ]
            raise BadRequest(json.dumps(error_messages))

    def get_value(self, key: str, default: Any = '') -> Any:
        """Get a value from validated_data with a default fallback."""
        return self.validated_data.get(key, default)
    
    def require_value(self, key: str) -> Any:
        """Get a required value from validated_data or raise ValidationError."""
        try:
            return self.validated_data[key]
        except KeyError:
            raise BadRequest(f'Missing required field: {key}')
        

def convert_to_utc(date_time):
    """Converts a datetime to UTC.
    
    - If naive, assumes Django's TIME_ZONE and makes it timezone-aware.
    - If aware but not UTC, converts it to UTC.
    - If already UTC, returns it unchanged.
    """
    
    # If datetime is naive, assume it's in Django’s TIME_ZONE and make it aware
    if timezone.is_naive(date_time):
        date_time = timezone.make_aware(date_time, timezone.get_current_timezone())
    
    # Convert to UTC if it’s not already UTC
    return date_time.astimezone(timezone.utc)