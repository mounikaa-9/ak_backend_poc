# models.py
from django.db import models
from users.models import User, Farm
from datetime import datetime

class Advisory(models.Model):
    """Main advisory model storing the complete advisory response"""
    
    # Foreign Keys
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='advisories')
    
    # Field Information
    field_id = models.CharField(max_length=50, db_index=True)
    field_name = models.CharField(max_length=255)
    field_area = models.DecimalField(max_digits=10, decimal_places=3)
    field_area_unit = models.CharField(max_length=20, default='acres')
    
    # Crop Information
    crop = models.CharField(max_length=100)
    sowing_date = models.DateField()
    
    # Advisory Information
    timestamp = models.BigIntegerField()  # Unix timestamp from API
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Satellite Data
    sar_day = models.CharField(max_length=20)
    sensed_day = models.DateField()
    last_satellite_visit = models.CharField(max_length=50)
    
    # Complete API Response as JSON in case something lost
    raw_response = models.JSONField(default=dict)
    
    # Extracted Key Data for quick access
    satellite_data = models.JSONField(default=dict)  # green, orange, red, purple, white
    advisory_data = models.JSONField(default=dict)  # The advisory object
    
    class Meta:
        db_table = 'advisories'
        ordering = ['-created_at']
        unique_together = ['farm', 'sensed_day']
        indexes = [
            models.Index(fields=['farm', '-created_at']),
            models.Index(fields=['field_id', '-created_at']),
            models.Index(fields=['crop', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.crop} - {self.field_name} - {self.created_at.date()}"
    
    def get_field_metadata(self):
        """Get field metadata in mock format"""
        return {
            "crop": self.crop,
            "fieldName": self.field_name,
            "fieldArea": f"{self.field_area} {self.field_area_unit}",
            "sowingDate": self.sowing_date.strftime('%Y-%m-%d'),
            "sarDay": self.sar_day,
            "lastSatelliteVisit": self.last_satellite_visit,
            "fieldId": self.field_id,
            "sensedDay": self.sensed_day.strftime('%Y-%m-%d'),
            "generatedOn": self.timestamp,
            "satelliteDataSummary": {
                "green": float(self.satellite_data.get('green', '0%').rstrip('%')),
                "orange": float(self.satellite_data.get('orange', '0%').rstrip('%')),
                "red": float(self.satellite_data.get('red', '0%').rstrip('%')),
                "purple": float(self.satellite_data.get('purple', '0%').rstrip('%')),
                "white": float(self.satellite_data.get('white', '0%').rstrip('%')),
            }
        }
    
    def get_fertilizer_advisory(self):
        """Get fertilizer advisory in mock format"""
        return {
            "advisory": {
                "Explanation of calculated parameters": {
                    "Fertilizers": self.advisory_data.get('Explanation of calculated parameters', {}).get('Fertilizers', [])
                },
                "Fertilizers": self.advisory_data.get('Explanation of calculated parameters', {}).get('Fertilizers', []),
                "Fertilizer": self.advisory_data.get('Fertilizer', {})
            }
        }
    
    def get_irrigation_advisory(self):
        """Get irrigation advisory in mock format"""
        return {
            "advisory": {
                "Explanation of calculated parameters": {
                    "Irrigation": self.advisory_data.get('Explanation of calculated parameters', {}).get('Irrigation', [])
                },
                "Irrigation": self.advisory_data.get('Irrigation', {})
            }
        }
    
    def get_growth_yield_advisory(self):
        """Get growth and yield advisory in mock format"""
        growth_data = self.advisory_data.get('Growth and Yield Estimation', {})
        explanation = self.advisory_data.get('Explanation of calculated parameters', {}).get('Growth and Yield Estimation', '')
        
        return {
            "advisory": {
                "Explanation of calculated parameters": {
                    "Growth and Yield Estimation": [explanation] if explanation else []
                },
                "Growth and Yield Estimation": growth_data
            }
        }
    
    def get_pest_disease_advisory(self):
        """Get pest and disease advisory in mock format"""
        return {
            "advisory": {
                "Explanation of calculated parameters": {
                    "Pest & Disease": self.advisory_data.get('Explanation of calculated parameters', {}).get('Pest & Disease', [])
                },
                "Pest and Disease": self.advisory_data.get('Pest and Disease', {})
            }
        }
    
    def get_weed_advisory(self):
        """Get weed advisory in mock format"""
        return {
            "advisory": {
                "Explanation of calculated parameters": {
                    "Weed": self.advisory_data.get('Explanation of calculated parameters', {}).get('Weed', '')
                },
                "Weed": self.advisory_data.get('Weed', {})
            }
        }
    
    def get_soil_management_advisory(self):
        """Get soil management advisory in mock format"""
        return {
            "advisory": {
                "Explanation of calculated parameters": {
                    "Soil Management": self.advisory_data.get('Explanation of calculated parameters', {}).get('Soil Management', [])
                },
                "Soil Management": self.advisory_data.get('Soil Management', {})
            }
        }