# Weather App Documentation

## Overview

The Weather app provides weather forecasting functionality for farms. It stores and retrieves comprehensive weather data including temperature, precipitation, humidity, wind, and astronomical information.

## Location

```
src/weather/
├── models.py           # WeatherPrediction model
├── api.py              # API endpoints
├── weather_schemas.py  # Validation schemas
├── utils.py            # Utility functions for saving data
├── admin.py            # Django admin configuration
├── apps.py             # App configuration
├── tests.py            # Test cases
└── migrations/         # Database migrations
```

## Models

### WeatherPrediction Model

**File:** `src/weather/models.py`

Stores weather forecast data for farms.

```python
class WeatherPrediction(models.Model):
    """
    Represents a single weather forecast or current day weather entry.
    All entries sharing the same weather_id and date_of_reload belong
    to one prediction batch (the current + future days).
    """
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| id | BigAutoField | Primary key |
| farm | ForeignKey(Farm) | Associated farm |
| date_of_reload | DateTimeField | When this forecast batch was fetched |
| date | DateField | Forecast date |
| is_current | BooleanField | Whether this is today's weather |

**Weather Description Fields:**

| Field | Type | Description |
|-------|------|-------------|
| summary | CharField(255) | Weather summary text |
| description | CharField(255) | Detailed weather description |
| main | CharField(50) | Main weather condition (e.g., "Clear", "Rain") |
| icon | CharField(10) | Weather icon code |

**Temperature Fields (in Celsius):**

| Field | Type | Description |
|-------|------|-------------|
| temp_day | FloatField | Daytime temperature |
| temp_min | FloatField | Minimum temperature |
| temp_max | FloatField | Maximum temperature |
| temp_morn | FloatField | Morning temperature |
| temp_eve | FloatField | Evening temperature |
| temp_night | FloatField | Nighttime temperature |

**Feels-Like Temperature Fields:**

| Field | Type | Description |
|-------|------|-------------|
| feels_like_day | FloatField | Feels-like temperature (day) |
| feels_like_morn | FloatField | Feels-like temperature (morning) |
| feels_like_eve | FloatField | Feels-like temperature (evening) |
| feels_like_night | FloatField | Feels-like temperature (night) |

**Environmental Fields:**

| Field | Type | Description |
|-------|------|-------------|
| humidity | FloatField | Humidity percentage |
| pressure | FloatField | Atmospheric pressure (hPa) |
| dew_point | FloatField | Dew point temperature |
| uvi | FloatField | UV index |
| wind_speed | FloatField | Wind speed (m/s) |
| wind_deg | IntegerField | Wind direction (degrees) |
| wind_gust | FloatField | Wind gust speed (nullable) |
| clouds | IntegerField | Cloud coverage percentage |
| pop | FloatField | Probability of precipitation (0-1) |
| rain | FloatField | Rain amount in mm (nullable) |

**Astronomical Fields:**

| Field | Type | Description |
|-------|------|-------------|
| sunrise | BigIntegerField | Sunrise time (Unix timestamp) |
| sunset | BigIntegerField | Sunset time (Unix timestamp) |
| moonrise | BigIntegerField | Moonrise time (Unix timestamp) |
| moonset | BigIntegerField | Moonset time (Unix timestamp) |
| moon_phase | FloatField | Moon phase (0-1) |

**Database Table:** Default (weather_weatherprediction)

**Constraints:**
- Unique together: `farm`, `date_of_reload`, `date`

**Indexes:**
- `date_of_reload`, `date`

**Ordering:** `date` (ascending)

---

## Schemas

**File:** `src/weather/weather_schemas.py`

### WeatherPredictionSchema

Complete weather data schema.

```python
class WeatherPredictionSchema(Schema):
    date: str
    is_current: bool
    summary: str
    description: str
    main: str
    icon: str
    temp_day: float
    temp_min: float
    temp_max: float
    temp_morn: float
    temp_eve: float
    temp_night: float
    feels_like_day: float
    feels_like_morn: float
    feels_like_eve: float
    feels_like_night: float
    humidity: float
    pressure: float
    dew_point: float
    uvi: float
    wind_speed: float
    wind_deg: float
    wind_gust: float
    clouds: float
    pop: float
    rain: float
    sunrise: float
    sunset: float
    moonrise: float
    moonset: float
    moon_phase: float
```

---

## API Endpoints

**Router:** `weather_router`
**Base Path:** `/api/weather`
**Tags:** `weather`

### Get Weather

```
GET /api/weather/get_weather
```

Retrieves weather predictions for a specific farm and date.

**Authentication:** JWT Required (or Django session auth)

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| field_id | string | Yes | The field_id from Farmanout |
| current_date | string | Yes | Date in YYYYMMDD format |

**Example Request:**
```
GET /api/weather/get_weather?field_id=1762238407649&current_date=20251029
```

**Response (200):**
```json
[
  {
    "date": "2025-10-29",
    "is_current": true,
    "summary": "Clear sky throughout the day",
    "description": "clear sky",
    "main": "Clear",
    "icon": "01d",
    "temp_day": 32.5,
    "temp_min": 24.2,
    "temp_max": 34.8,
    "temp_morn": 26.3,
    "temp_eve": 30.1,
    "temp_night": 25.5,
    "feels_like_day": 34.2,
    "feels_like_morn": 27.8,
    "feels_like_eve": 31.5,
    "feels_like_night": 26.2,
    "humidity": 65.0,
    "pressure": 1012.0,
    "dew_point": 22.5,
    "uvi": 8.5,
    "wind_speed": 3.2,
    "wind_deg": 180,
    "wind_gust": 5.1,
    "clouds": 10,
    "pop": 0.1,
    "rain": 0.0,
    "sunrise": 1698548400,
    "sunset": 1698590400,
    "moonrise": 1698552000,
    "moonset": 1698598800,
    "moon_phase": 0.5
  },
  {
    "date": "2025-10-30",
    "is_current": false,
    "summary": "Partly cloudy with light rain",
    "description": "light rain",
    "main": "Rain",
    "icon": "10d",
    "temp_day": 28.5,
    "temp_min": 22.1,
    "temp_max": 30.2,
    "...": "..."
  }
]
```

**Response Notes:**
- Returns an array of weather predictions
- First entry with `is_current: true` represents today's weather
- Subsequent entries are forecasts for upcoming days
- Typically includes 7-8 days of forecast data

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | Farm not found |
| 400 | Invalid date format (expected YYYYMMDD) |
| 404 | No weather data found for this date |

---

## Utility Functions

**File:** `src/weather/utils.py`

### save_weather_from_response

Saves weather data from the external API response.

```python
def save_weather_from_response(weather_data: dict, field_id: str)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| weather_data | dict | Weather API response |
| field_id | str | The field ID |

**Expected Input Format:**
```json
{
  "weather": {
    "daily": [
      {
        "dt": 1698580800,
        "summary": "Clear sky throughout the day",
        "weather": [
          {
            "description": "clear sky",
            "main": "Clear",
            "icon": "01d"
          }
        ],
        "temp": {
          "day": 32.5,
          "min": 24.2,
          "max": 34.8,
          "morn": 26.3,
          "eve": 30.1,
          "night": 25.5
        },
        "feels_like": {
          "day": 34.2,
          "morn": 27.8,
          "eve": 31.5,
          "night": 26.2
        },
        "humidity": 65,
        "pressure": 1012,
        "dew_point": 22.5,
        "uvi": 8.5,
        "wind_speed": 3.2,
        "wind_deg": 180,
        "wind_gust": 5.1,
        "clouds": 10,
        "pop": 0.1,
        "rain": 0.0,
        "sunrise": 1698548400,
        "sunset": 1698590400,
        "moonrise": 1698552000,
        "moonset": 1698598800,
        "moon_phase": 0.5
      }
    ]
  }
}
```

**Behavior:**
- Gets current datetime as `date_of_reload`
- Converts Unix timestamp to date for each day
- First entry (index 0) marked as `is_current=True`
- Uses default value `-1` for missing fields
- Creates new records (does not update existing)

---

## Database Operations

### Creating Weather Records

```python
from weather.models import WeatherPrediction
from users.models import Farm
from datetime import datetime, date

farm = Farm.objects.get(field_id="1762238407649")

WeatherPrediction.objects.create(
    farm=farm,
    date_of_reload=datetime.now(),
    date=date(2025, 10, 29),
    is_current=True,
    summary="Clear sky",
    description="clear sky",
    main="Clear",
    icon="01d",
    temp_day=32.5,
    temp_min=24.2,
    temp_max=34.8,
    temp_morn=26.3,
    temp_eve=30.1,
    temp_night=25.5,
    feels_like_day=34.2,
    feels_like_morn=27.8,
    feels_like_eve=31.5,
    feels_like_night=26.2,
    humidity=65.0,
    pressure=1012.0,
    dew_point=22.5,
    uvi=8.5,
    wind_speed=3.2,
    wind_deg=180,
    wind_gust=5.1,
    clouds=10,
    pop=0.1,
    rain=0.0,
    sunrise=1698548400,
    sunset=1698590400,
    moonrise=1698552000,
    moonset=1698598800,
    moon_phase=0.5
)
```

### Querying Weather Data

```python
from datetime import date

# Get all predictions for a specific reload date
weather_data = WeatherPrediction.objects.filter(
    farm=farm,
    date_of_reload__date=date(2025, 10, 29)
).order_by("date")

# Get current day weather
current = WeatherPrediction.objects.filter(
    farm=farm,
    is_current=True
).order_by("-date_of_reload").first()

# Get latest weather batch
latest_reload = WeatherPrediction.objects.filter(
    farm=farm
).order_by("-date_of_reload").first()

if latest_reload:
    all_predictions = WeatherPrediction.objects.filter(
        farm=farm,
        date_of_reload=latest_reload.date_of_reload
    ).order_by("date")
```

---

## Weather Icons

Common weather icon codes returned by the API:

| Icon | Description |
|------|-------------|
| 01d/01n | Clear sky (day/night) |
| 02d/02n | Few clouds |
| 03d/03n | Scattered clouds |
| 04d/04n | Broken clouds |
| 09d/09n | Shower rain |
| 10d/10n | Rain |
| 11d/11n | Thunderstorm |
| 13d/13n | Snow |
| 50d/50n | Mist |

---

## Moon Phase Values

| Value | Phase |
|-------|-------|
| 0, 1 | New moon |
| 0.25 | First quarter |
| 0.5 | Full moon |
| 0.75 | Last quarter |

---

## Flood Detection Logic

The weather data is used in crop loss analytics to detect flood conditions:

```python
# Flood condition check (from pipelines)
is_flood_condition = (
    weather_response
    and "daily" in weather_response
    and len(weather_response["daily"]) > 0
    and float(weather_response["daily"][0].get("rain", -1)) > 75
)
```

Flood analytics are created when:
- Rain exceeds 75mm in the current day's forecast
- Active flood analytics are extended if rain continues

---

## Related Documentation

- [API Reference](./API_REFERENCE.md) - Complete API documentation
- [Database Structure](./DATABASE.md) - Database schema details
- [Integrations](./INTEGRATIONS.md) - External API integration details
- [Crop Loss Analytics](./CROP_LOSS_ANALYTICS.md) - Crop loss tracking using weather data
