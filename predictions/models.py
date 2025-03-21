from uuid import uuid4
from djongo import models


class CyclePreditction(models.Model):
    user_id_hash = models.CharField(max_length=200, primary_key=True, editable=False)
    cycle_length = models.IntegerField()
    period_duration = models.IntegerField()
    next_period_start = models.DateTimeField()
    next_period_end = models.DateTimeField()
    days_until_next_period = models.IntegerField()
    update_datetime = models.DateTimeField(auto_now=True)



    
