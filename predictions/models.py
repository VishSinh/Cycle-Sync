from uuid import uuid4
from djongo import models

class PeriodPredictions(models.Model):
    class Meta:
        db_table = 'period_predictions'
        managed = False
    
    period_prediction_id = models.UUIDField(primary_key=True, editable=False, default=uuid4)   
    user_id_hash = models.CharField(max_length=100)
    user_data = models.JSONField()
    prediction_data = models.JSONField()
    create_datetime = models.DateTimeField(auto_now_add=True)
    
class CycleStatPrediction(models.Model):
    class Meta:
        db_table = 'cycle_stat_prediction'
        managed = False
    
    cycle_stat_prediction_id = models.UUIDField(primary_key=True, editable=False, default=uuid4)  
    user_id_hash = models.CharField(max_length=100)
    average_cycle_length = models.JSONField()
    period_statistics = models.JSONField()
    next_period_prediction = models.JSONField()
    create_datetime = models.DateTimeField(auto_now_add=True)

    
