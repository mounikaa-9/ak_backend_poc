from django.db import models

from users.models import Farm

class IndexTimeSeries(models.Model):
    """Time series data for various satellite values"""
    INDEX_CHOICES = [
        ('rvi', 'RVI - Ratio Vegetation Index'),
        ('ndvi', 'NDVI - Normalized Difference Vegetation Index'),
        ('savi', 'SAVI - Soil Adjusted Vegetation Index'),
        ('evi', 'EVI - Enhanced Vegetation Index'),
        ('ndre', 'NDRE - Normalized Difference Red Edge'),
        ('rsm', 'RSM - Root Zone Soil Moisture'),
        ('ndwi', 'NDWI - Normalized Difference Water Index'),
        ('ndmi', 'NDMI - Normalized Difference Moisture Index'),
        ('evapo', 'ET - Evapotranspiration'),
        ('soc', 'SOC - Soil Organic Carbon'),
        ('etci', 'ETCI')
    ]
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='index_time_series')
    index_type = models.CharField(max_length=10, choices=INDEX_CHOICES)
    date = models.DateField()
    value = models.DecimalField(max_digits=6, decimal_places=2, null = True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'index_time_series'
        unique_together = ['farm', 'index_type', 'date']
        ordering = ['date']
    
    def __str__(self):
        return f"{self.farm.field_name} - {self.index_type} - {self.date}"


class Heatmap(models.Model):
    """Heatmap images storage"""
    INDEX_CHOICES = [
        ('rvi', 'RVI'),
        ('ndvi', 'NDVI'),
        ('savi', 'SAVI'),
        ('evi', 'EVI'),
        ('ndre', 'NDRE'),
        ('rsm', 'RSM'),
        ('ndwi', 'NDWI'),
        ('ndmi', 'NDMI'),
        ('evapo', 'ET'),
        ('soc', 'SOC'),
        ('etci', 'ETCI'),
        ('hybrid', 'HYBRID')
    ]
    
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='heatmaps')
    index_type = models.CharField(max_length=10, choices=INDEX_CHOICES)
    date = models.DateField()
    image_url = models.URLField(max_length=500, null = True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'heatmaps'
        unique_together = ['farm', 'index_type', 'date']
    
    def __str__(self):
        return f"{self.farm.field_name} - {self.index_type} - {self.date}"