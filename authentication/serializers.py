from rest_framework import serializers

from utils.exceptions import BadRequest


class AuthenticationSerializer(serializers.Serializer):
    auth_type = serializers.IntegerField(min_value=1, max_value=2)
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def to_internal_value(self, data):
        # Override this method to customize how errors are formatted
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as exc:
            # Format the errors as you did in the view
            errors = exc.detail
            message = "; ".join([errors[key][0] if key == "non_field_errors" else f"{key} - {errors[key][0]}" for key in errors])
            raise BadRequest(message)

