from django.forms import model_to_dict
from rest_framework.views import APIView
from cycles.models import CurrentPeriod

from users.models import  User, UserDetails
from utils.helpers import format_response, get_serialized_data
from utils.exceptions import CustomException
from users.serializers import AddUserDetailsSerializer, FetchUserDetailsSerializer


class AddUserDetailsView(APIView):
    add_user_details_serialzier = AddUserDetailsSerializer
    
    @format_response
    def post(self, request):
        request_body = self.add_user_details_serialzier(data=request.data)
        request_body.is_valid(raise_exception=True)

        user_id_hash = get_serialized_data(request_body, 'user_id_hash')
        first_name = get_serialized_data(request_body, 'first_name')
        last_name = get_serialized_data(request_body, 'last_name')
        dob = get_serialized_data(request_body, 'dob', None)
        height = get_serialized_data(request_body, 'height', None)
        weight = get_serialized_data(request_body, 'weight', None)
        
        user = User.objects.get(user_id_hash=user_id_hash)
        if not user:
            raise CustomException('Invalid user')
        
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
    fetch_user_details_serializer = FetchUserDetailsSerializer

    @format_response
    def post(self, request):
        request_body = self.fetch_user_details_serializer(data=request.data)
        request_body.is_valid(raise_exception=True)
        
        user_id_hash =get_serialized_data(request_body, 'user_id_hash')
        
        user_details = UserDetails.objects.get(user_id_hash=user_id_hash)
        if not user_details:
            raise CustomException('User details not found')
        
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
       
