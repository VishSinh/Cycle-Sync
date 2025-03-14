from rest_framework import serializers

from utils.helpers import BaseSerializer


class CreatePeriodRecordSerializer(BaseSerializer):
    event = serializers.IntegerField(min_value=1, max_value=2)
    date_time = serializers.DateTimeField(required=False)
    
    
class CreateSymptomsRecordSerializer(BaseSerializer):
    symptom = serializers.CharField(max_length=200)
    comments = serializers.CharField(max_length=500)
    
    
class FetchSymptomsRecordsSerializer(BaseSerializer):
    user_id_hash = serializers.CharField(max_length=255)
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    rows_per_page = serializers.IntegerField(min_value=10, max_value=100, required=False, default=10)
    symptom_occurence = serializers.IntegerField(min_value=0, max_value=2, required=False, default=0)
    create_datetime_start = serializers.DateTimeField(required=False)
    create_datetime_end = serializers.DateTimeField(required=False)
    
    
class FetchPeriodRecordDetailsSerializer(BaseSerializer):
    user_id_hash = serializers.CharField(max_length=255)
    period_record_id = serializers.CharField(max_length=255)
    
        