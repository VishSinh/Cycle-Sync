from djongo import models


class ActiveSessions(models.Model):
    class Meta:
        db_table = 'active_sessions'
        
    user_id_hash = models.CharField(max_length=200, primary_key=True, editable=False)
    session_id = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    
class TrackerNonRegisteredUserRequests(models.Model):
    class Meta:
        db_table = 'tracker_non_registered_user_requests'
        
    ip_address = models.CharField(max_length=200, primary_key=True, editable=False)
    count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
class TrackerRegisteredUserRequests(models.Model):
    class Meta:
        db_table = 'tracker_registered_user_requests'
        
    user_id_hash = models.CharField(max_length=200, primary_key=True, editable=False)
    ip_address = models.CharField(max_length=200)
    count = models.IntegerField(default=0)
    freq_count = models.IntegerField(default=0)
    freq_req_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
