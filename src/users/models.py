from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models

class User(AbstractUser):
    """standard Django authentication"""
    def __str__(self):
        return self.username
    
class Farm(models.Model):
    """Farm/Field information"""
    """
    Important:
    farm_id -> unique id in the database
    field_id -> unique id given by the farmanout's api
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farms')
    farm_email = models.EmailField()
    farm_coordinates = models.JSONField()
    field_id = models.CharField(max_length=50, unique=True)
    field_name = models.CharField(max_length=100)
    field_area = models.DecimalField(max_digits=10, decimal_places=2, help_text="Area in hectares")
    crop = models.CharField(max_length=50)
    sowing_date = models.DateField()
    
    last_sensed_day = models.DateField(null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'farms'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.field_name} - {self.user.username}"