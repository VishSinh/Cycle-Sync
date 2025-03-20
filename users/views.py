from django.forms import model_to_dict
from rest_framework.views import APIView
from cycles.models import CurrentPeriod, PeriodRecord

from users.models import  User, UserDetails
from utils.helpers import convert_to_utc, forge, get_serialized_data
from utils.exceptions import BadRequest, ResourceNotFound
from users.serializers import AddUserDetailsSerializer, UserDetailsPatchSerializer


class UserDetailsView(APIView):
    
    @forge
    def get(self, request):
        user_id_hash = request.user_obj.user_id_hash
        
        user_details = UserDetails.objects.filter(user_id_hash=user_id_hash).first()
        if not user_details:
            response = {'exists': False}
            return response
        
        response = model_to_dict(user_details)
        
        user = User.objects.get(user_id_hash=user_id_hash)
        response['email'] = user.email
        
        current_period = CurrentPeriod.objects.filter(user_id_hash=user_id_hash)
        if current_period:
            current_period = current_period[0]
            response['current_period_record_id']  = current_period.current_period_record_id
            response['last_period_record_id'] = current_period.last_period_record_id
        else:
            response['current_period_record_id']  = None
            response['last_period_record_id'] = None
        response['exists'] = True
        return response  
    
    @forge
    def post(self, request):
        serializer = AddUserDetailsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id_hash = request.user_obj.user_id_hash
        first_name = serializer.get_value('first_name')
        last_name = serializer.get_value('last_name')
        dob = serializer.get_value('dob', None)
        height = serializer.get_value('height', None)
        weight = serializer.get_value('weight', None)
        last_period_start = serializer.get_value('last_period_start', None)
        ongoing_period = serializer.get_value('ongoing_period', False)
        last_period_end = serializer.get_value('last_period_end', None)
        
        start_datetime = convert_to_utc(last_period_start)
        if not ongoing_period:
            end_datetime = convert_to_utc(last_period_end)
        
        user = User.objects.filter(user_id_hash=user_id_hash).first()
        if not user:
            raise ResourceNotFound('Invalid user')
        
        # Check if user details already exist
        user_details = UserDetails.objects.filter(user_id_hash=user_id_hash).first()
        if user_details:
            raise BadRequest('User details already exist')
        
        UserDetails.objects.create(
            user_id_hash=user_id_hash,
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            height=height,
            weight=weight
        )
        
        period_record = PeriodRecord.objects.create(
            user_id_hash=user_id_hash,
            current_status=PeriodRecord.CurrentStatus.ONGOING if ongoing_period else PeriodRecord.CurrentStatus.COMPLETED,
            start_datetime=start_datetime,
            end_datetime=end_datetime # This will be None if ongoing_period is True
        )
        
        CurrentPeriod.objects.create(
            user_id_hash=user_id_hash,
            current_period_record_id=period_record.period_record_id if ongoing_period else None,
            last_period_record_id=None if ongoing_period else period_record.period_record_id
        )
        
        
        
        return {'message': 'User details added successfully'}
    
    
    @forge
    def patch(self, request):
        serializer = UserDetailsPatchSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        first_name = serializer.get_value('first_name', None)
        last_name = serializer.get_value('last_name', None)
        dob = serializer.get_value('dob', None)
        height = serializer.get_value('height', None)
        weight = serializer.get_value('weight', None)
        
        user_id_hash = request.user_obj.user_id_hash
        user_details = UserDetails.objects.filter(user_id_hash=user_id_hash).first()
        if not user_details:
            raise ResourceNotFound('User details not found')
        
        if first_name:
            user_details.first_name = first_name
        if last_name:
            user_details.last_name = last_name
        if dob:
            user_details.dob = dob
        if height:
            user_details.height = height
        if weight:
            user_details.weight = weight
            
        user_details.save()
        
        return {'message': 'User details updated successfully'}

         
       
