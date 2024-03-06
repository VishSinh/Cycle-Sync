from rest_framework import serializers


class AuthenticationSerializer(serializers.Serializer):
    auth_type = serializers.IntegerField(min_value=1, max_value=2)
    email = serializers.EmailField()
    password = serializers.CharField()

