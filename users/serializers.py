from rest_framework import serializers

from utils.helpers import BaseSerializer

class AddUserDetailsSerializer(BaseSerializer):
    user_id_hash = serializers.CharField(max_length=255)
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
    dob = serializers.DateField(required=False)
    height = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    weight = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    
class FetchUserDetailsSerializer(BaseSerializer):
    user_id_hash = serializers.CharField(max_length=255)