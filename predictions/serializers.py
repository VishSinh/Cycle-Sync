from rest_framework import serializers

from predictions.models import PeriodPredictions


class CreatePredictionSerializer(serializers.Serializer):
    user_id_hash = serializers.CharField(max_length=255)
    user_data = serializers.JSONField()
    
class CreateCycleStatPredictionSerializer(serializers.Serializer):
    user_id_hash = serializers.CharField(max_length=255)