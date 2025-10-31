from ninja import Router
from ninja.errors import HttpError
from ninja.security import django_auth
from ninja_jwt.authentication import JWTAuth
from datetime import datetime

from users.models import Farm
from weather.models import WeatherPrediction
from weather.weather_schemas import WeatherPredictionSchema

weather_router = Router(tags=["weather"])

@weather_router.get(
    path="/get_weather",
    auth=[JWTAuth(), django_auth],
    response=list[WeatherPredictionSchema],
)
def get_weather(request, field_id: str, current_date: str):
    """
    Get all weather predictions for a given farm and date_of_reload.
    """
    try:
        farm = Farm.objects.get(field_id=field_id)
    except Farm.DoesNotExist:
        raise HttpError(400, "Farm not found")

    try:
        datetime.strptime(current_date, "%Y%m%d").date()
    except ValueError:
        raise HttpError(400, "Invalid date format. Expected YYYYMMDD.")

    weather_qs = WeatherPrediction.objects.filter(
        farm=farm,
        date_of_reload__date=current_date 
    ).order_by("date")

    if not weather_qs.exists():
        raise HttpError(404, "No weather data found for this date")

    return [
        WeatherPredictionSchema(
            date=w.date.strftime("%Y-%m-%d"),
            is_current=w.is_current,
            summary=w.summary,
            description=w.description,
            main=w.main,
            icon=w.icon,
            temp_day=w.temp_day,
            temp_min=w.temp_min,
            temp_max=w.temp_max,
            temp_morn=w.temp_morn,
            temp_eve=w.temp_eve,
            temp_night=w.temp_night,
            feels_like_day=w.feels_like_day,
            feels_like_morn=w.feels_like_morn,
            feels_like_eve=w.feels_like_eve,
            feels_like_night=w.feels_like_night,
            humidity=w.humidity,
            pressure=w.pressure,
            dew_point=w.dew_point,
            uvi=w.uvi,
            wind_speed=w.wind_speed,
            wind_deg=w.wind_deg,
            wind_gust=w.wind_gust,
            clouds=w.clouds,
            pop=w.pop,
            rain=w.rain,
            sunrise=w.sunrise,
            sunset=w.sunset,
            moonrise=w.moonrise,
            moonset=w.moonset,
            moon_phase=w.moon_phase,
        )
        for w in weather_qs
    ]
