from uuid import uuid4
from djongo import models


class ActiveSessions(models.Model):
    class Meta:
        db_table = 'active_sessions'
        
    user_id_hash = models.CharField(max_length=200, primary_key=True, editable=False)
    session_id = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
