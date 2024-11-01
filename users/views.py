from django.forms import model_to_dict
from rest_framework.views import APIView
from cycles.models import CurrentPeriod

from users.models import  User, UserDetails
from utils.logger import logger
from utils.helpers import format_response, get_serialized_data
from utils.exceptions import BadRequest, NotFound
from users.serializers import AddUserDetailsSerializer


class AddUserDetailsView(APIView):
    
    @format_response
    def post(self, request):
        serializer = AddUserDetailsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id_hash = request.user_id_hash
        first_name = serializer.get_value('first_name')
        last_name = serializer.get_value('last_name')
        dob = serializer.get_value('dob', None)
        height = serializer.get_value('height', None)
        weight = serializer.get_value('weight', None)
        
        user = User.objects.filter(user_id_hash=user_id_hash).first()
        if not user:
            raise NotFound('Invalid user')
        
        user_details, created = UserDetails.objects.update_or_create(
            user_id_hash=user_id_hash,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'dob': dob,
                'height': height,
                'weight': weight
            }
        )

        user_details.save()
        
        response_body = model_to_dict(user_details)
        message = 'User details added successfully' if created else 'User details updated successfully'
        code = 201 if created else 200
        response_body['message'] = message 
        return  response_body, code


class FetchUserDetails(APIView):

    @format_response
    def get(self, request):
        user_id_hash = request.user_id_hash
        
        user_details = UserDetails.objects.filter(user_id_hash=user_id_hash).first()
        if not user_details:
            raise NotFound('User details not found')
        
        response_body = model_to_dict(user_details)
        
        user = User.objects.get(user_id_hash=user_id_hash)
        response_body['email'] = user.email
        
        current_period = CurrentPeriod.objects.filter(user_id_hash=user_id_hash)
        if current_period:
            current_period = current_period[0]
            response_body['current_period_record_id']  = current_period.current_period_record_id
            response_body['last_period_record_id'] = current_period.last_period_record_id
        else:
            response_body['current_period_record_id']  = None
            response_body['last_period_record_id'] = None

        return response_body       
       
