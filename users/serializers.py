from rest_framework import serializers

from utils.helpers import BaseSerializer

class AddUserDetailsSerializer(BaseSerializer):
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    dob = serializers.DateField(required=False)
    height = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    weight = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    ongoing_period = serializers.BooleanField(required=False)
    last_period_start = serializers.DateTimeField()
    last_period_end = serializers.DateTimeField(required=False)
    
    # Create a function to ensure either ongoing_period is False and last_period_end is provided or ongoing_period is True and last_period_end is not provided
    def validate(self, data):
        ongoing_period = data.get('ongoing_period')
        last_period_end = data.get('last_period_end')
        
        if ongoing_period and last_period_end:
            raise serializers.ValidationError('last_period_end should not be provided when ongoing_period is True')
        
        if not ongoing_period and not last_period_end:
            raise serializers.ValidationError('last_period_end should be provided when ongoing_period is False')
        
        return data
    
class UserDetailsPatchSerializer(BaseSerializer):
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    dob = serializers.DateField(required=False)
    height = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    weight = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    