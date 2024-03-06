from uuid import uuid4
from djongo import models
from django_enumfield import enum


class User(models.Model):
    class Meta:
        db_table = 'user'
    
    user_id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user_id_hash = models.CharField(max_length=200)
    email = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=200)
    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)
    
class UserDetails(models.Model):
    class Meta:
        db_table = 'user_details'
        
    user_id_hash = models.CharField(max_length=200, primary_key=True, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    
 
    
