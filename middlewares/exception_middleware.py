import json
from typing import Any
from utils.helpers import APIResponse
from rest_framework import status
import uuid
from django.http import HttpRequest, HttpResponse
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied as DjangoPermissionDenied

from utils.logger import logger

class ExceptionMiddleware:
    def __init__(self, get_response: Any = None) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        correlation_id = str(uuid.uuid4())
        request.correlation_id = correlation_id  # type: ignore

        response = self.get_response(request)

        if not isinstance(response, HttpResponse):
            response = HttpResponse(
                content=json.dumps(response),
                content_type='application/json',
                status=200
            )

        response['X-Correlation-ID'] = correlation_id
        return response

    def process_exception(self, request: HttpRequest, exception: Exception) -> HttpResponse:
        logger.error(exception)
        
        if not hasattr(exception, 'status_code'):
            logger.info('Exception does not have status code')
            exception.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        return APIResponse(
            success=False,
            status_code=exception.status_code,
            error=exception
        ).response(correlation_id=getattr(request, 'correlation_id', None))
        
        

