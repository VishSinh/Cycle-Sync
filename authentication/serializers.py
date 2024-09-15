from rest_framework import serializers

from utils.helpers import BaseSerializer


class AuthenticationSerializer(BaseSerializer):
    auth_type = serializers.IntegerField(min_value=1, max_value=2)
    email = serializers.EmailField()
    password = serializers.CharField()
    

