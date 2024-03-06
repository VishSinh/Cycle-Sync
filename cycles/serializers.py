from rest_framework import serializers


class CreatePeriodRecordSerializer(serializers.Serializer):
    user_id_hash = serializers.CharField(max_length=255)
    event = serializers.IntegerField(min_value=1, max_value=2)

class FetchPeriodRecordsSerializer(serializers.Serializer):
    user_id_hash = serializers.CharField(max_length=255)
    page = serializers.IntegerField(min_value=1)
    rows_per_page = serializers.IntegerField(min_value=10, max_value=100)
    start_datetime = serializers.DateTimeField(required=False)
    end_datetime = serializers.DateTimeField(required=False)
    
class CreateSymptomsRecordSerializer(serializers.Serializer):
    user_id_hash = serializers.CharField(max_length=255)
    symptom = serializers.CharField(max_length=200)
    comments = serializers.CharField(max_length=500)
    
class FetchSymptomsRecordsSerializer(serializers.Serializer):
    user_id_hash = serializers.CharField(max_length=255)
    page = serializers.IntegerField(min_value=1)
    rows_per_page = serializers.IntegerField(min_value=10, max_value=100)
    symptom_occurence = serializers.IntegerField(min_value=0, max_value=2)
    create_datetime_start = serializers.DateTimeField(required=False)
    create_datetime_end = serializers.DateTimeField(required=False)
    
class FetchPeriodRecordDetailsSerializer(serializers.Serializer):
    user_id_hash = serializers.CharField(max_length=255)
    period_record_id = serializers.CharField(max_length=255)
    
        