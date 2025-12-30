# Crop Loss Analytics App Documentation

## Overview

The Crop Loss Analytics app tracks and monitors potential crop loss scenarios including floods, droughts, and pest infestations. It automatically creates and updates analytics records based on weather data, satellite indices, and AI advisory information.

## Location

```
src/crop_loss_analytics/
├── models.py                      # CropLossAnalytics model
├── api.py                         # API endpoints
├── crop_loss_analytics_schema.py  # Validation schemas
├── admin.py                       # Django admin configuration
├── apps.py                        # App configuration
├── tests.py                       # Test cases
└── migrations/                    # Database migrations
```

## Models

### CropLossAnalytics Model

**File:** `src/crop_loss_analytics/models.py`

Tracks crop loss scenarios for farms.

```python
class CropLossAnalytics(models.Model):
    """Crop loss tracking for flood, drought, and pest scenarios"""
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| id | BigAutoField | Primary key |
| farm | ForeignKey(Farm) | Associated farm |
| kind | CharField(20) | Type of loss scenario (see INDEX_CHOICES) |
| is_active | BooleanField | Whether the scenario is currently active |
| date_start | DateField | When the scenario started |
| date_current | DateField | Current date of analysis |
| date_end | DateField | Projected end date |
| closest_date_sensed | DateField | Nearest satellite observation date |
| metadata | JSONField | Additional tracking data |

**INDEX_CHOICES:**

| Code | Full Name | Description |
|------|-----------|-------------|
| `flood` | Flood Scenario | High rainfall/flooding conditions |
| `drought` | Drought Case | Low moisture/drought conditions |
| `pest` | Pest Case | Pest infestation detected |

**Database Table:** Default (crop_loss_analytics_croplossanalytics)

**Constraints:**
- Unique together: `farm`, `kind`, `is_active`

---

## Schemas

**File:** `src/crop_loss_analytics/crop_loss_analytics_schema.py`

### CropLossAnalyticsResponseSchema

Response schema for crop loss analytics.

```python
class CropLossAnalyticsResponseSchema(Schema):
    start_date: Optional[date]
    approx_end_date: Optional[date]
    kind: str
```

---

## API Endpoints

**Router:** `crop_loss_analytics_router`
**Base Path:** `/api/crop_loss_analytics`
**Tags:** `Crop Loss Analytics`

### Get Crop Loss Analytics

```
GET /api/crop_loss_analytics/crop_loss_analytics
```

Retrieves active crop loss analytics for a specific scenario type.

**Authentication:** JWT Required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| kind | string (Literal) | Yes | One of: "flood", "pest", "drought" |

**Example Request:**
```
GET /api/crop_loss_analytics/crop_loss_analytics?kind=flood
```

**Response (200) - Active scenario found:**
```json
{
  "start_date": "2025-10-25",
  "approx_end_date": "2025-10-29",
  "kind": "flood"
}
```

**Response (200) - No active scenario:**
```json
{
  "start_date": null,
  "approx_end_date": null,
  "kind": "flood"
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | Farm not found |

---

## Scenario Detection Logic

The crop loss analytics are created and updated by the data processing pipelines. Each scenario has specific trigger conditions:

### Flood Scenario

**Trigger Condition:**
- Rain > 75mm in the current day's weather forecast

**File:** `src/pipelines/new_profile_script.py` - `create_flood_analytics()`

```python
is_flood_condition = (
    weather_response
    and "daily" in weather_response
    and len(weather_response["daily"]) > 0
    and float(weather_response["daily"][0].get("rain", -1)) > 75
)
```

**Behavior:**
- **New scenario**: Creates record with 3-day projected duration
- **Existing active**: Extends end date by 3 days if flood continues
- **Deactivation**: Marks inactive if no flood for 4+ days after end date
- **Updates**: Tracks closest sensed date to projected end

---

### Drought Scenario

**Trigger Condition:**
- NDMI (Normalized Difference Moisture Index) < 30 for 4 consecutive satellite visits

**File:** `src/pipelines/new_profile_script.py` - `create_drought_analytics()`

```python
high_drought_condition = (
    float(index_values.get("ndmi", -1)) != -1
    and float(index_values["ndmi"]) < 30
)
```

**Behavior:**
- **Creation**: Requires 4 consecutive visits with NDMI < 30
- **New scenario**: Creates record with 30-day projected duration
- **Existing active**: Extends end date by 30 days if drought continues
- **Deactivation**: Marks inactive after 4 consecutive visits without drought
- **Metadata tracking**:
  - `consecutive_drought_visits`: Count of drought detections
  - `consecutive_no_drought_visits`: Count of non-drought visits
  - `total_satellite_visits`: Total visits tracked

---

### Pest Scenario

**Trigger Condition:**
- High probability pest detection in AI advisory for 4 consecutive satellite visits

**File:** `src/pipelines/new_profile_script.py` - `create_pest_analytics()`

```python
def has_high_probability_pest(data: dict) -> bool:
    """Check if AI response has high probability pest detection"""
    try:
        pests = data.get("Pest and Disease", {}).get("potential_pests", [])
        for pest in pests:
            if pest.get("probability", "").lower() == "high":
                return True
    except Exception:
        pass
    return False
```

**Behavior:**
- **Creation**: Requires 4 consecutive advisories with high-probability pests
- **New scenario**: Creates record with 3-day projected duration
- **Existing active**: Extends end date by 3 days if pests continue
- **Deactivation**: Marks inactive after 4 consecutive visits without pests
- **Metadata tracking**:
  - `consecutive_pest_visits`: Count of pest detections
  - `consecutive_no_pest_visits`: Count of non-pest visits
  - `total_visits`: Total visits tracked

---

## Scenario Lifecycle

```
               [Trigger Detected]
                      │
                      ▼
          ┌─────────────────────┐
          │  Check Consecutive  │
          │  Conditions (4x)    │
          └─────────────────────┘
                      │
                      ▼ (4 consecutive)
          ┌─────────────────────┐
          │  CREATE ANALYTICS   │
          │  is_active = True   │
          └─────────────────────┘
                      │
                      ▼
          ┌─────────────────────┐
          │  MONITOR (Active)   │◄────────────┐
          └─────────────────────┘             │
                      │                       │
          ┌───────────┴───────────┐           │
          │                       │           │
          ▼                       ▼           │
   [Condition Still Met]    [Condition Gone] │
          │                       │           │
          ▼                       ▼           │
   Extend date_end        Increment no_*     │
   Reset no_* counter     counter            │
          │                       │           │
          └───────────────────────┴───────────┘
                      │
                      ▼ (4 consecutive without condition)
          ┌─────────────────────┐
          │  DEACTIVATE         │
          │  is_active = False  │
          └─────────────────────┘
```

---

## Database Operations

### Creating Analytics Records

```python
from crop_loss_analytics.models import CropLossAnalytics
from users.models import Farm
from datetime import datetime, timedelta

farm = Farm.objects.get(field_id="1762238407649")

# Create flood analytics
CropLossAnalytics.objects.create(
    farm=farm,
    kind="flood",
    is_active=True,
    date_start=datetime.now().date(),
    date_current=datetime.now().date(),
    date_end=(datetime.now() + timedelta(days=3)).date(),
    closest_date_sensed=datetime.now().date(),
    metadata={}
)

# Create drought analytics with metadata
CropLossAnalytics.objects.create(
    farm=farm,
    kind="drought",
    is_active=True,
    date_start=datetime.now().date(),
    date_current=datetime.now().date(),
    date_end=(datetime.now() + timedelta(days=30)).date(),
    closest_date_sensed=datetime.now().date(),
    metadata={
        'consecutive_drought_visits': 4,
        'consecutive_no_drought_visits': 0,
        'total_satellite_visits': 4
    }
)
```

### Querying Analytics

```python
# Get active analytics for a specific kind
active_flood = CropLossAnalytics.objects.filter(
    farm=farm,
    kind="flood",
    is_active=True
).first()

# Get all active analytics for a farm
active_analytics = CropLossAnalytics.objects.filter(
    farm=farm,
    is_active=True
)

# Get historical analytics (all including inactive)
all_analytics = CropLossAnalytics.objects.filter(farm=farm)

# Check if any active scenario exists
has_active = CropLossAnalytics.objects.filter(
    farm=farm,
    is_active=True
).exists()
```

### Updating Analytics

```python
# Update existing analytics
analytics = CropLossAnalytics.objects.get(farm=farm, kind="drought", is_active=True)
analytics.date_current = datetime.now().date()
analytics.date_end = (datetime.now() + timedelta(days=30)).date()
analytics.metadata['consecutive_drought_visits'] += 1
analytics.save()

# Deactivate analytics
analytics.is_active = False
analytics.save()
```

---

## Metadata Structure

### Drought Metadata

```json
{
  "consecutive_drought_visits": 5,
  "consecutive_no_drought_visits": 0,
  "total_satellite_visits": 8
}
```

### Pest Metadata

```json
{
  "consecutive_pest_visits": 4,
  "consecutive_no_pest_visits": 0,
  "total_visits": 6
}
```

### Flood Metadata

Flood analytics typically don't use metadata since the condition is based on single-day weather rather than consecutive observations.

---

## Threshold Reference

| Scenario | Trigger Threshold | Creation Requirement | Duration | Deactivation |
|----------|-------------------|---------------------|----------|--------------|
| Flood | Rain > 75mm | Single occurrence | 3 days | 4 days after end date |
| Drought | NDMI < 30 | 4 consecutive visits | 30 days | 4 consecutive visits without |
| Pest | High probability | 4 consecutive visits | 3 days | 4 consecutive visits without |

---

## Integration with Pipelines

The crop loss analytics are automatically managed by the data processing pipelines:

1. **Profile Creation Pipeline** (`pipelines/new_profile_script.py`)
   - Called when new satellite data is available
   - Fetches weather, index values, and advisory data
   - Creates/updates analytics based on conditions

2. **Weather-Only Update**
   - Called when no new satellite data but weather needs updating
   - Only updates flood analytics

```python
# In update_all_data()
await sync_to_async(create_flood_analytics)(farm, weather_response, field_id, last_day_sensed)
await sync_to_async(create_drought_analytics)(farm, index_values, field_id, last_day_sensed)
await sync_to_async(create_pest_analytics)(farm, ai_response, field_id, last_day_sensed)
```

---

## Related Documentation

- [API Reference](./API_REFERENCE.md) - Complete API documentation
- [Database Structure](./DATABASE.md) - Database schema details
- [Pipelines](./PIPELINES.md) - Data processing pipeline details
- [Weather](./WEATHER.md) - Weather data for flood detection
- [Heatmaps](./HEATMAPS.md) - Index values for drought detection
- [AI Advisory](./AI_ADVISORY.md) - Advisory data for pest detection
