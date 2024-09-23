from rest_framework import serializers

from utils.helpers import BaseSerializer

class CreatePredictionSerializer(BaseSerializer):
    user_id_hash = serializers.CharField(max_length=255)
    user_data = serializers.JSONField()
    
class CreateCycleStatPredictionSerializer(BaseSerializer):
    user_id_hash = serializers.CharField(max_length=255)
