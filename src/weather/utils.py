import os
import django
import json
from datetime import datetime, timezone
from django.db import transaction
from weather.models import WeatherPrediction
from users.models import Farm

def save_weather_from_response(weather_data: dict, field_id : str):
    """
    Save satellite index image URLs into the Heatmap model.

    Args:
        field_data (dict): JSON response containing satellite URLs and metadata.
    Raises:
        ValueError: If required metadata is missing or invalid.
        Farm.DoesNotExist: If the specified farm is not found.
    """
    farm = Farm.objects.get(field_id = field_id)
    date_of_reload = datetime.now()

    for i, day in enumerate(weather_data.get("weather", {}).get("daily", None)):
        if day is None:
            continue
        WeatherPrediction.objects.create(
            farm = farm,
            date_of_reload=date_of_reload,
            date=datetime.fromtimestamp(day["dt"]),
            is_current=(i == 0),
            summary=day.get("summary", "NA"),
            description=day.get("weather", [{}])[0].get("description", "NA"),
            main=day.get("weather", [{}])[0].get("main", "NA"),
            icon=day.get("weather", [{}])[0].get("icon", "NA"),
            temp_day=day.get("temp", {}).get("day", -1),
            temp_min=day.get("temp", {}).get("min", -1),
            temp_max=day.get("temp", {}).get("max", -1),
            temp_morn=day.get("temp", {}).get("morn", -1),
            temp_eve=day.get("temp", {}).get("eve", -1),
            temp_night=day.get("temp", {}).get("night", -1),
            feels_like_day=day.get("feels_like", {}).get("day", -1),
            feels_like_morn=day.get("feels_like", {}).get("morn", -1),
            feels_like_eve=day.get("feels_like", {}).get("eve", -1),
            feels_like_night=day.get("feels_like", {}).get("night", -1),
            humidity=day.get("humidity", -1),
            pressure=day.get("pressure", -1),
            dew_point=day.get("dew_point", -1),
            uvi=day.get("uvi", -1),
            wind_speed=day.get("wind_speed", -1),
            wind_deg=day.get("wind_deg", -1),
            wind_gust=day.get("wind_gust", -1),
            clouds=day.get("clouds", -1),
            pop=day.get("pop", -1),
            rain=day.get("rain", -1),
            sunrise=day.get("sunrise", -1),
            sunset=day.get("sunset", -1),
            moonrise=day.get("moonrise", -1),
            moonset=day.get("moonset", -1),
            moon_phase=day.get("moon_phase", -1),
        )