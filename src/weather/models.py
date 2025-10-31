from django.db import models
from django.utils import timezone
import uuid
from users.models import Farm


class WeatherPrediction(models.Model):
    """
    Represents a single weather forecast or current day weather entry.
    All entries sharing the same weather_id and date_of_reload belong
    to one prediction batch (the current + future days).
    """
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='weather_prediction')
    # When this forecast batch was fetched
    date_of_reload = models.DateTimeField(default=timezone.now, db_index=True)
    # daily forecast date
    date = models.DateField()
    # Whether this is the "current" day's record or prediction
    is_current = models.BooleanField(default=False)

    # Weather data
    summary = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    main = models.CharField(max_length=50)
    icon = models.CharField(max_length=10)

    # Temperature info
    temp_day = models.FloatField()
    temp_min = models.FloatField()
    temp_max = models.FloatField()
    temp_morn = models.FloatField()
    temp_eve = models.FloatField()
    temp_night = models.FloatField()

    # Feels-like info
    feels_like_day = models.FloatField()
    feels_like_morn = models.FloatField()
    feels_like_eve = models.FloatField()
    feels_like_night = models.FloatField()

    # Other environmental parameters
    humidity = models.FloatField()
    pressure = models.FloatField()
    dew_point = models.FloatField()
    uvi = models.FloatField()
    wind_speed = models.FloatField()
    wind_deg = models.IntegerField()
    wind_gust = models.FloatField(null=True, blank=True)
    clouds = models.IntegerField()
    pop = models.FloatField()  # probability of precipitation
    rain = models.FloatField(null=True, blank=True)

    # Astronomical data
    sunrise = models.BigIntegerField()
    sunset = models.BigIntegerField()
    moonrise = models.BigIntegerField()
    moonset = models.BigIntegerField()
    moon_phase = models.FloatField()

    class Meta:
        ordering = ["date"]
        unique_together = ["farm", "date_of_reload", "date"]
        indexes = [
            models.Index(fields=["date_of_reload", "date"]),
        ]

    def __str__(self):
        return f"{self.date} ({'Current' if self.is_current else 'Forecast'})"
