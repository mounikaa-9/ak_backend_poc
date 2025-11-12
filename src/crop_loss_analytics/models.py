from django.db import models

from users.models import Farm

class CropLossAnalytics(models.Model):
    
    INDEX_CHOICES = [
        ('flood', 'Flood Scenario'),
        ('drought', 'Drought Case'),
        ('pest', 'Pest Case'),
    ]
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, verbose_name="Crop Loss Analytics")
    kind = models.CharField(max_length=20, choices=INDEX_CHOICES)
    is_active = models.BooleanField(default=True)
    date_start = models.DateField()
    date_current = models.DateField()
    date_end = models.DateField()
    closest_date_sensed = models.DateField()
    
    metadata = models.JSONField(default=dict, blank=True)
    class Meta:
        unique_together = ["farm", "kind", "is_active"]