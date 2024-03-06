from datetime import datetime
from traceback import print_exc
from django.forms import model_to_dict
from rest_framework.views import APIView
from rest_framework import status
from cycles.models import CurrentPeriod
from django.utils.decorators import method_decorator

from users.models import  User, UserDetails
from period_tracking_BE.helpers.utils import get_serialized_data, response_obj, validate_token
from period_tracking_BE.helpers.exceptions import CustomException
from users.serializers import AddUserDetailsSerializer, FetchUserDetailsSerializer

@method_decorator(validate_token, name='post')
class AddUserDetailsView(APIView):
    add_user_details_serialzier = AddUserDetailsSerializer
    
    def post(self, request):
        try:
            request_body = self.add_user_details_serialzier(data=request.data)
            
            ########## HANDLE VALIDATION ERROR ##########
            if not request_body.is_valid():
                errors = request_body.errors
                message = "; ".join([errors[key][0] if key == "non_field_errors" else f"{key} - {errors[key][0]}" for key in errors])
                return response_obj(success=False, message=message, status_code=status.HTTP_400_BAD_REQUEST)
            #############################################
            
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
            
            request_body = model_to_dict(user_details)
            message = 'User details added successfully' if created else 'User details updated successfully'
            return response_obj(message=message, data=request_body)
        
        except CustomException as e:
            return response_obj(success=False, message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print_exc(e)
            return response_obj(success=False, message='An error occured', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
@method_decorator(validate_token, name='post')
class FetchUserDetails(APIView):
    fetch_user_details_serializer = FetchUserDetailsSerializer
    
    def post(self, request):
        try:
            request_body = self.fetch_user_details_serializer(data=request.data)
            
            ########## HANDLE VALIDATION ERROR ##########
            if not request_body.is_valid():
                errors = request_body.errors
                message = "; ".join([errors[key][0] if key == "non_field_errors" else f"{key} - {errors[key][0]}" for key in errors])
                return response_obj(success=False, message=message, status_code=status.HTTP_400_BAD_REQUEST)
            #############################################
            
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

            return response_obj(message='User details fetched successfully', data=response_body)
        
        except CustomException as e:
            return response_obj(success=False, message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            print_exc(e)
            return response_obj(success=False, message='An error occured', status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
