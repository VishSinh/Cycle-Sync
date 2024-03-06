from djongo import models
from django_enumfield import enum
from uuid import uuid4

class PeriodRecord(models.Model):
    class Meta:
        db_table = 'period_record'
        
    class Event(enum.Enum):
        START = 1
        END = 2
    
    class CurrentStatus(enum.Enum):
        ONGOING = 1
        COMPLETED = 2 
        
    period_record_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user_id_hash = models.CharField(max_length=200)
    current_status = enum.EnumField(CurrentStatus, default=CurrentStatus.ONGOING)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    
class CurrentPeriod(models.Model):
    class Meta:
        db_table = 'current_period'
        
    user_id_hash = models.CharField(max_length=200, primary_key=True, editable=False)
    current_period_record_id = models.CharField(max_length=200, null=True, blank=True)
    last_period_record_id = models.CharField(max_length=200, null=True, blank=True)
    
    
class SymptomsRecord(models.Model):
    class Meta:
        db_table = 'symptoms_record'
        
    class SymptomOccurence(enum.Enum):
        DURING_PERIOD = 1
        NON_CYCLE_PHASE = 2
    
    symptom_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user_id_hash = models.CharField(max_length=200)
    symptom = models.CharField(max_length=200)
    comments = models.TextField()
    symptom_occurence = enum.EnumField(SymptomOccurence)
    period_record_id = models.CharField(max_length=200, null=True, blank=True)
    created_datetime = models.DateTimeField(auto_now_add=True)
   
