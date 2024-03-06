from hashlib import sha256
from rest_framework.response import Response

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
    

