# Database Structure Documentation

## Overview

The AK Backend POC uses PostgreSQL as its primary database. The schema is managed through Django's ORM with migrations for version control.

## Database Configuration

**File:** `src/ak_backend_poc/settings.py`

```python
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}
```

**Connection Settings:**
- `conn_max_age`: 600 seconds (10 minutes) - connection pooling
- `conn_health_checks`: Enabled - validates connections before use

**Environment Variable:**
```
DATABASE_URL=postgresql://user:password@host:port/dbname
```

---

## Entity Relationship Diagram

```
┌─────────────────┐
│      User       │
│  (auth_user)    │
│─────────────────│
│ id (PK)         │
│ username        │
│ email           │
│ password        │
│ ...             │
└────────┬────────┘
         │
         │ 1:1 (unique)
         ▼
┌─────────────────┐
│      Farm       │
│    (farms)      │
│─────────────────│
│ id (PK)         │
│ user_id (FK)    │──────────────────────────────────────────────┐
│ field_id        │                                              │
│ field_name      │                                              │
│ field_area      │                                              │
│ crop            │                                              │
│ sowing_date     │                                              │
│ last_sensed_day │                                              │
│ farm_coordinates│                                              │
│ farm_email      │                                              │
│ created_at      │                                              │
│ updated_at      │                                              │
└────────┬────────┘                                              │
         │                                                        │
         │ 1:N                                                    │
         ├──────────────────┬──────────────────┬─────────────────┤
         │                  │                  │                  │
         ▼                  ▼                  ▼                  ▼
┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ IndexTimeSeries│ │    Heatmap     │ │   Advisory     │ │WeatherPrediction│
│(index_time_    │ │   (heatmaps)   │ │  (advisories)  │ │                │
│    series)     │ │                │ │                │ │                │
│────────────────│ │────────────────│ │────────────────│ │────────────────│
│ id (PK)        │ │ id (PK)        │ │ id (PK)        │ │ id (PK)        │
│ farm_id (FK)   │ │ farm_id (FK)   │ │ farm_id (FK)   │ │ farm_id (FK)   │
│ index_type     │ │ index_type     │ │ field_id       │ │ date_of_reload │
│ date           │ │ date           │ │ sensed_day     │ │ date           │
│ value          │ │ image_url      │ │ crop           │ │ is_current     │
│ created_at     │ │ created_at     │ │ advisory_data  │ │ temp_*         │
└────────────────┘ └────────────────┘ │ satellite_data │ │ humidity       │
                                      │ raw_response   │ │ rain           │
                                      │ ...            │ │ ...            │
                                      └────────────────┘ └────────────────┘
         │
         │ 1:N
         ▼
┌────────────────────┐
│ CropLossAnalytics  │
│────────────────────│
│ id (PK)            │
│ farm_id (FK)       │
│ kind               │
│ is_active          │
│ date_start         │
│ date_current       │
│ date_end           │
│ closest_date_sensed│
│ metadata           │
└────────────────────┘
```

---

## Tables

### users_user (User)

Custom user model extending Django's AbstractUser.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PRIMARY KEY, AUTO | User ID |
| username | varchar(150) | UNIQUE, NOT NULL | Username |
| email | varchar(254) | NOT NULL | Email address |
| password | varchar(128) | NOT NULL | Hashed password |
| first_name | varchar(150) | | First name |
| last_name | varchar(150) | | Last name |
| is_active | boolean | DEFAULT true | Account active |
| is_staff | boolean | DEFAULT false | Staff access |
| is_superuser | boolean | DEFAULT false | Superuser access |
| date_joined | timestamp with tz | NOT NULL | Registration date |
| last_login | timestamp with tz | | Last login time |

---

### farms

Farm/field information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PRIMARY KEY, AUTO | Farm ID (internal) |
| user_id | bigint | FOREIGN KEY (users_user), UNIQUE | Owner |
| farm_email | varchar(254) | NOT NULL | Contact email |
| farm_coordinates | jsonb | NOT NULL | Polygon coordinates |
| field_id | varchar(50) | UNIQUE, NOT NULL | Farmanout field ID |
| field_name | varchar(100) | NOT NULL | Field name |
| field_area | decimal(10,2) | NOT NULL | Area in hectares |
| crop | varchar(50) | NOT NULL | Crop type |
| sowing_date | date | NOT NULL | Sowing date |
| last_sensed_day | date | | Last satellite observation |
| created_at | timestamp with tz | AUTO | Creation timestamp |
| updated_at | timestamp with tz | AUTO | Update timestamp |

**Indexes:**
- `farms_user_id_key` (UNIQUE) on `user_id`
- `farms_field_id_key` (UNIQUE) on `field_id`

---

### index_time_series

Satellite vegetation index time series data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PRIMARY KEY, AUTO | Record ID |
| farm_id | bigint | FOREIGN KEY (farms) | Associated farm |
| index_type | varchar(10) | NOT NULL | Index type code |
| date | date | NOT NULL | Observation date |
| value | decimal(6,2) | | Index value (nullable) |
| created_at | timestamp with tz | AUTO | Creation timestamp |

**Index Type Values:** `rvi`, `ndvi`, `savi`, `evi`, `ndre`, `rsm`, `ndwi`, `ndmi`, `evapo`, `soc`, `etci`

**Constraints:**
- UNIQUE (`farm_id`, `index_type`, `date`)

**Indexes:**
- `index_time_series_farm_id_index_type_date_key` (UNIQUE)

---

### heatmaps

Satellite heatmap image URLs.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PRIMARY KEY, AUTO | Record ID |
| farm_id | bigint | FOREIGN KEY (farms) | Associated farm |
| index_type | varchar(10) | NOT NULL | Index type code |
| date | date | NOT NULL | Observation date |
| image_url | varchar(500) | | Azure Blob Storage URL |
| created_at | timestamp with tz | AUTO | Creation timestamp |

**Index Type Values:** `rvi`, `ndvi`, `savi`, `evi`, `ndre`, `rsm`, `ndwi`, `ndmi`, `evapo`, `soc`, `etci`, `hybrid`

**Constraints:**
- UNIQUE (`farm_id`, `index_type`, `date`)

**Indexes:**
- `heatmaps_farm_id_index_type_date_key` (UNIQUE)

---

### advisories

AI agricultural advisory data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PRIMARY KEY, AUTO | Record ID |
| farm_id | bigint | FOREIGN KEY (farms) | Associated farm |
| field_id | varchar(50) | NOT NULL, INDEXED | Farmanout field ID |
| field_name | varchar(255) | NOT NULL | Field name |
| field_area | decimal(10,3) | NOT NULL | Field area |
| field_area_unit | varchar(20) | DEFAULT 'acres' | Area unit |
| crop | varchar(100) | NOT NULL | Crop type |
| sowing_date | date | NOT NULL | Sowing date |
| timestamp | bigint | NOT NULL | API generation timestamp |
| created_at | timestamp with tz | AUTO | Record creation timestamp |
| sar_day | varchar(20) | NOT NULL | SAR observation day |
| sensed_day | date | NOT NULL | Satellite observation date |
| last_satellite_visit | varchar(50) | NOT NULL | Last visit info |
| raw_response | jsonb | DEFAULT '{}' | Complete API response |
| satellite_data | jsonb | DEFAULT '{}' | Satellite health data |
| advisory_data | jsonb | DEFAULT '{}' | Parsed advisory data |

**Constraints:**
- UNIQUE (`farm_id`, `sensed_day`)

**Indexes:**
- `advisories_farm_id_sensed_day_key` (UNIQUE)
- `advisories_farm_id_created_at_idx` on (`farm_id`, `created_at` DESC)
- `advisories_field_id_created_at_idx` on (`field_id`, `created_at` DESC)
- `advisories_crop_created_at_idx` on (`crop`, `created_at` DESC)

---

### weather_weatherprediction

Weather forecast data.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PRIMARY KEY, AUTO | Record ID |
| farm_id | bigint | FOREIGN KEY (farms) | Associated farm |
| date_of_reload | timestamp with tz | NOT NULL, INDEXED | Fetch timestamp |
| date | date | NOT NULL | Forecast date |
| is_current | boolean | DEFAULT false | Today's weather flag |
| summary | varchar(255) | NOT NULL | Weather summary |
| description | varchar(255) | NOT NULL | Detailed description |
| main | varchar(50) | NOT NULL | Main condition |
| icon | varchar(10) | NOT NULL | Weather icon code |
| temp_day | float | NOT NULL | Daytime temperature |
| temp_min | float | NOT NULL | Minimum temperature |
| temp_max | float | NOT NULL | Maximum temperature |
| temp_morn | float | NOT NULL | Morning temperature |
| temp_eve | float | NOT NULL | Evening temperature |
| temp_night | float | NOT NULL | Night temperature |
| feels_like_day | float | NOT NULL | Feels-like (day) |
| feels_like_morn | float | NOT NULL | Feels-like (morning) |
| feels_like_eve | float | NOT NULL | Feels-like (evening) |
| feels_like_night | float | NOT NULL | Feels-like (night) |
| humidity | float | NOT NULL | Humidity % |
| pressure | float | NOT NULL | Pressure hPa |
| dew_point | float | NOT NULL | Dew point |
| uvi | float | NOT NULL | UV index |
| wind_speed | float | NOT NULL | Wind speed m/s |
| wind_deg | integer | NOT NULL | Wind direction |
| wind_gust | float | | Wind gust (nullable) |
| clouds | integer | NOT NULL | Cloud coverage % |
| pop | float | NOT NULL | Precipitation probability |
| rain | float | | Rain amount mm (nullable) |
| sunrise | bigint | NOT NULL | Sunrise timestamp |
| sunset | bigint | NOT NULL | Sunset timestamp |
| moonrise | bigint | NOT NULL | Moonrise timestamp |
| moonset | bigint | NOT NULL | Moonset timestamp |
| moon_phase | float | NOT NULL | Moon phase (0-1) |

**Constraints:**
- UNIQUE (`farm_id`, `date_of_reload`, `date`)

**Indexes:**
- `weather_weatherprediction_farm_id_date_of_reload_date_key` (UNIQUE)
- `weather_weatherprediction_date_of_reload_date_idx` on (`date_of_reload`, `date`)

---

### crop_loss_analytics_croplossanalytics

Crop loss scenario tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | bigint | PRIMARY KEY, AUTO | Record ID |
| farm_id | bigint | FOREIGN KEY (farms) | Associated farm |
| kind | varchar(20) | NOT NULL | Scenario type |
| is_active | boolean | DEFAULT true | Active status |
| date_start | date | NOT NULL | Scenario start date |
| date_current | date | NOT NULL | Current analysis date |
| date_end | date | NOT NULL | Projected end date |
| closest_date_sensed | date | NOT NULL | Nearest observation date |
| metadata | jsonb | DEFAULT '{}' | Tracking metadata |

**Kind Values:** `flood`, `drought`, `pest`

**Constraints:**
- UNIQUE (`farm_id`, `kind`, `is_active`)

---

## JSON Field Structures

### farm_coordinates (farms)

Polygon coordinates for the field boundary:

```json
[
  [15.678440, 77.756490],
  [15.678199, 77.757107],
  [15.679233, 77.757575],
  [15.679458, 77.757124],
  [15.679185, 77.756507]
]
```

Format: `[[latitude, longitude], ...]`

---

### satellite_data (advisories)

Satellite health classification percentages:

```json
{
  "green": "65.5%",
  "orange": "20.3%",
  "red": "5.2%",
  "purple": "4.0%",
  "white": "5.0%"
}
```

---

### advisory_data (advisories)

Parsed advisory recommendations:

```json
{
  "Fertilizer": {
    "nitrogen": {"amount": 25, "unit": "kg/ha"},
    "phosphorus": {"amount": 15, "unit": "kg/ha"}
  },
  "Irrigation": {
    "recommended": true,
    "amount": "30mm"
  },
  "Growth and Yield Estimation": {
    "growth_stage": "vegetative",
    "estimated_yield": "4.5 tons/ha"
  },
  "Pest and Disease": {
    "potential_pests": [
      {"name": "stem borer", "probability": "high"}
    ]
  },
  "Weed": {
    "weed_pressure": "moderate"
  },
  "Soil Management": {
    "soil_health": "good"
  },
  "Explanation of calculated parameters": {
    "Fertilizers": ["explanation..."],
    "Irrigation": ["explanation..."]
  }
}
```

---

### metadata (crop_loss_analytics)

Tracking data for consecutive observations:

**Drought:**
```json
{
  "consecutive_drought_visits": 5,
  "consecutive_no_drought_visits": 0,
  "total_satellite_visits": 8
}
```

**Pest:**
```json
{
  "consecutive_pest_visits": 4,
  "consecutive_no_pest_visits": 0,
  "total_visits": 6
}
```

---

## Migrations

Each app has its own migrations folder:

```
src/
├── users/migrations/
│   ├── 0001_initial.py
│   ├── 0002_farm_last_sensed_day.py
│   └── 0003_alter_farm_user.py
├── heatmaps/migrations/
│   ├── 0001_initial.py
│   ├── 0002_*.py
│   └── 0003_*.py
├── ai_advisory/migrations/
│   └── 0001_initial.py
├── weather/migrations/
│   └── 0001_initial.py
└── crop_loss_analytics/migrations/
    ├── 0001_initial.py
    ├── 0002_*.py
    ├── 0003_*.py
    └── 0004_croplossanalytics_metadata.py
```

**Running Migrations:**
```bash
cd src
python manage.py migrate
```

**Creating New Migrations:**
```bash
python manage.py makemigrations <app_name>
```

---

## Database Operations

### Creating Records

```python
from users.models import User, Farm
from heatmaps.models import IndexTimeSeries, Heatmap
from ai_advisory.models import Advisory
from weather.models import WeatherPrediction
from crop_loss_analytics.models import CropLossAnalytics

# Create user
user = User.objects.create(username="farmer", email="farmer@example.com")

# Create farm
farm = Farm.objects.create(
    user=user,
    field_id="123456",
    farm_email="farmer@example.com",
    ...
)

# Create related records
IndexTimeSeries.objects.create(farm=farm, index_type="ndvi", date="2025-10-29", value=0.65)
```

### Bulk Operations

```python
# Bulk create
IndexTimeSeries.objects.bulk_create([
    IndexTimeSeries(farm=farm, index_type="ndvi", date="2025-10-29", value=0.65),
    IndexTimeSeries(farm=farm, index_type="savi", date="2025-10-29", value=0.48),
])

# Update or create
Heatmap.objects.update_or_create(
    farm=farm,
    index_type="ndvi",
    date="2025-10-29",
    defaults={"image_url": "https://..."}
)
```

### Transactions

```python
from django.db import transaction

with transaction.atomic():
    # All operations in this block are atomic
    farm.last_sensed_day = "2025-10-29"
    farm.save()
    IndexTimeSeries.objects.create(...)
    Heatmap.objects.create(...)
```

---

## Related Documentation

- [Users](./USERS.md) - User and Farm models
- [Heatmaps](./HEATMAPS.md) - IndexTimeSeries and Heatmap models
- [AI Advisory](./AI_ADVISORY.md) - Advisory model
- [Weather](./WEATHER.md) - WeatherPrediction model
- [Crop Loss Analytics](./CROP_LOSS_ANALYTICS.md) - CropLossAnalytics model
