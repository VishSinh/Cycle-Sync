from rest_framework import status


class BadRequest(Exception):
    status_code = status.HTTP_400_BAD_REQUEST
    message = 'The request is invalid or malformed'
    
    
class Unauthorized(Exception):
    status_code = status.HTTP_401_UNAUTHORIZED
    message = 'You are not authorized to access this resource'
    
    
class TooManyRequests(Exception):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    message = 'You have exceeded the rate limit'
    

class ResourceNotFound(Exception):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    message = 'The requested resource was not found'
    

class Conflict(Exception):
    status_code = status.HTTP_409_CONFLICT
    message = 'The request conflicts with the current state of the resource'
    

class Forbidden(Exception):
    status_code = status.HTTP_403_FORBIDDEN
    message = 'You are not authorized to access this resource'
    

class InternalServerError(Exception):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = 'An internal server error occurred'