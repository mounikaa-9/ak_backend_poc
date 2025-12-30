# Pipelines Module Documentation

## Overview

The Pipelines module provides data processing workflows for farm profile creation and updates. It orchestrates the fetching of satellite data, AI advisory, and weather information, storing the results in the database and triggering crop loss analytics.

## Location

```
src/pipelines/
├── __init__.py
├── new_profile_script.py       # Async profile creation pipeline
└── sync/
    ├── __init__.py
    └── sync_new_profile.py     # Synchronous profile creation pipeline
```

## Available Pipelines

| Pipeline | Type | Endpoint | Description |
|----------|------|----------|-------------|
| Async Pipeline | Async | `/api/pipelines/create_entire_profile` | Full async profile update |
| Sync Pipeline | Sync | `/api/pipelines/sync/sync_create_entire_profile` | Synchronous profile update with detailed status |

---

## Async Pipeline

**File:** `src/pipelines/new_profile_script.py`

### Overview

The async pipeline uses concurrent async operations for maximum performance. It leverages `asyncio.gather()` to run multiple data fetching operations in parallel.

### API Endpoint

```
POST /api/pipelines/create_entire_profile
```

**Authentication:** JWT Required

**Request Body:**
```json
{
  "field_id": "1762238407649",
  "farm_email": "john@farm.com",
  "field_name": "North Field",
  "field_area": 5.25,
  "crop": "rice",
  "sowing_date": "2025-10-01",
  "last_sensed_day": "2025-10-29",
  "farm_coordinates": [
    [15.678440, 77.756490],
    [15.678199, 77.757107]
  ]
}
```

**Response (Full Update):**
```json
{
  "status": "success",
  "field_id": "1762238407649",
  "last_sensed_day": "20251029",
  "update_type": "full"
}
```

**Response (Weather Only):**
```json
{
  "status": "success",
  "field_id": "1762238407649",
  "last_sensed_day": "20251029",
  "update_type": "weather_only"
}
```

### Pipeline Flow

```
                    [API Request]
                         │
                         ▼
                  ┌──────────────┐
                  │ Get Farm by  │
                  │ user & field │
                  └──────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ Fetch Last   │
                  │ Sensed Day   │
                  └──────────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
     [New Sensed Day?]     [No New Sensed Day]
              │                     │
              ▼                     ▼
     ┌────────────────┐    ┌─────────────────┐
     │  FULL UPDATE   │    │ WEATHER ONLY    │
     │  (Concurrent)  │    │ UPDATE          │
     └────────────────┘    └─────────────────┘
              │                     │
   ┌──────────┼──────────┐         │
   │          │          │         │
   ▼          ▼          ▼         ▼
┌──────┐ ┌──────┐ ┌──────┐    ┌──────┐
│Heat- │ │Index │ │AI    │    │Weath-│
│maps  │ │Values│ │Advis.│    │er    │
└──────┘ └──────┘ └──────┘    └──────┘
   │          │          │         │
   └──────────┴──────────┘         │
              │                     │
              ▼                     │
    ┌─────────────────┐            │
    │ CROP LOSS       │◄───────────┘
    │ ANALYTICS       │
    │ - Flood         │
    │ - Drought       │
    │ - Pest          │
    └─────────────────┘
```

### Processing Functions

#### process_heatmaps

```python
async def process_heatmaps(field_id: str, sensed_day: str)
```

1. Fetches all heatmap images from Farmanout API
2. Uploads images to Azure Blob Storage
3. Saves Azure URLs to Heatmap model

#### process_index_values

```python
async def process_index_values(field_id: str, sensed_day: str) -> dict
```

1. Fetches satellite index values from Farmanout API
2. Saves values to IndexTimeSeries model
3. Returns index values for analytics

#### process_ai_advisory

```python
async def process_ai_advisory(field_id: str, crop: str) -> dict
```

1. Fetches AI advisory from Farmanout API
2. Saves advisory to Advisory model
3. Returns advisory data for pest analytics

#### process_weather

```python
async def process_weather(field_id: str) -> dict
```

1. Fetches weather forecast from Farmanout API
2. Saves forecast to WeatherPrediction model
3. Returns weather data for flood analytics

### Full Update Function

```python
async def update_all_data(farm: Farm, field_id: str, crop: str, new_sensed_day: str)
```

Runs all four processing functions concurrently:

```python
results = await asyncio.gather(
    process_heatmaps(field_id, new_sensed_day),
    process_index_values(field_id, new_sensed_day),
    process_ai_advisory(field_id, crop),
    process_weather(field_id),
    return_exceptions=True
)
```

Then creates/updates crop loss analytics:
- `create_flood_analytics()` - Based on weather data
- `create_drought_analytics()` - Based on NDMI values
- `create_pest_analytics()` - Based on AI advisory

### Weather-Only Update

```python
async def update_weather_only(farm: Farm, field_id: str, crop: str, last_day_sensed: str)
```

Called when no new satellite data is available:
1. Fetches and saves weather data
2. Updates only flood analytics (weather-based)

---

## Sync Pipeline

**File:** `src/pipelines/sync/sync_new_profile.py`

### Overview

The sync pipeline provides a synchronous alternative with detailed status tracking for each operation. It runs operations sequentially using `asyncio.run()` for each async call.

### API Endpoint

```
POST /api/pipelines/sync/sync_create_entire_profile
```

**Authentication:** JWT Required

**Request Body:** Same as async pipeline

**Response (Full Update):**
```json
{
  "status": "success",
  "field_id": "1762238407649",
  "last_sensed_day": "20251029",
  "update_type": "full",
  "results": {
    "heatmaps": {"success": true, "error": null},
    "index_values": {"success": true, "error": null, "data": {...}},
    "ai_advisory": {"success": true, "error": null, "data": {...}},
    "weather": {"success": true, "error": null, "data": {...}},
    "flood_analytics": {"success": true, "error": null, "action": "created"},
    "drought_analytics": {"success": false, "error": null, "action": "none"},
    "pest_analytics": {"success": false, "error": null, "action": "none"}
  },
  "summary": {
    "successful": 5,
    "total": 7
  }
}
```

### Key Differences from Async

| Aspect | Async Pipeline | Sync Pipeline |
|--------|---------------|---------------|
| Execution | Concurrent | Sequential |
| Performance | Faster | Slower |
| Error Tracking | Basic logging | Detailed per-operation status |
| Response | Simple status | Full results breakdown |
| Use Case | Production | Debugging/monitoring |

### Processing Functions (Sync)

Each function returns a detailed result dictionary:

```python
def process_heatmaps(field_id: str, sensed_day: str) -> Dict[str, Any]:
    result = {"success": False, "error": None}
    try:
        # ... processing ...
        result["success"] = True
    except Exception as e:
        result["error"] = str(e)
    return result
```

---

## Crop Loss Analytics Creation

### create_flood_analytics

**File:** `src/pipelines/new_profile_script.py`

```python
def create_flood_analytics(
    farm: Farm,
    weather_response: dict,
    field_id: str,
    last_day_sensed: datetime
)
```

**Trigger:** Rain > 75mm in today's forecast

**Logic:**
1. Check if rain exceeds 75mm
2. If existing active flood analytics:
   - Update `closest_date_sensed` if closer to `date_end`
   - Extend `date_end` by 3 days if flood continues
   - Mark inactive if no flood for 4+ days after `date_end`
3. If no existing and flood detected:
   - Find previous heatmap date for `date_start`
   - Create new analytics with 3-day duration

### create_drought_analytics

```python
def create_drought_analytics(
    farm: Farm,
    index_values: dict,
    field_id: str,
    last_day_sensed: datetime
)
```

**Trigger:** NDMI < 30 for 4 consecutive visits

**Logic:**
1. Check if NDMI < 30 (high drought condition)
2. If existing active drought analytics:
   - Update `closest_date_sensed` if closer
   - Track consecutive drought/no-drought visits in metadata
   - Extend `date_end` by 30 days if drought continues
   - Mark inactive after 4 consecutive non-drought visits
3. If no existing and drought detected:
   - Check last 4 NDMI values for consecutive drought
   - Create only if 4 consecutive visits with NDMI < 30
   - Set 30-day duration

### create_pest_analytics

```python
def create_pest_analytics(
    farm: Farm,
    ai_response: dict,
    field_id: str,
    last_day_sensed: datetime
)
```

**Trigger:** High probability pest for 4 consecutive advisories

**Logic:**
1. Check for high probability pest in advisory
2. If existing active pest analytics:
   - Update `closest_date_sensed` if closer
   - Track consecutive pest/no-pest visits in metadata
   - Extend `date_end` by 3 days if pests continue
   - Mark inactive after 4 consecutive non-pest visits
3. If no existing and pest detected:
   - Check last 4 advisories for consecutive high-probability pests
   - Create only if 4 consecutive detections
   - Set 3-day duration

---

## Helper Functions

### has_high_probability_pest

```python
def has_high_probability_pest(data: dict) -> bool
```

Checks if AI advisory contains high-probability pest detection:

```python
pests = data.get("Pest and Disease", {}).get("potential_pests", [])
for pest in pests:
    if pest.get("probability", "").lower() == "high":
        return True
return False
```

### Date Normalization

```python
def normalize_to_yyyymmdd(date_value) -> str
```

Converts various date formats to YYYYMMDD string:

```python
return str(date_value).replace('-', '').replace('/', '')[:8]
```

---

## Azure Upload Integration

The pipeline integrates with Azure Blob Storage for heatmap images:

**File:** `src/utils/az_upload.py`

### upload_field_images_to_azure

```python
def upload_field_images_to_azure(
    field_data: dict,
    exclude_types: List[str] = None
) -> Dict[str, any]
```

**Process:**
1. Downloads images from Farmanout (Google Cloud Storage)
2. Uploads to Azure Blob Storage container "farm-images"
3. Returns Azure URLs for storage in database

**Storage Structure:**
```
farm-images/
└── {field_id}/
    └── {sensed_day}/
        ├── ndvi.png
        ├── savi.png
        ├── evi.png
        └── ...
```

---

## Error Handling

All pipeline functions include comprehensive error handling:

```python
try:
    # Operation
except Exception as e:
    logger.error(f"Operation failed: {e}")
    traceback.print_exc()
    # Return error info or raise HttpError
```

**HTTP Errors:**

| Status | Condition |
|--------|-----------|
| 404 | Farm not found |
| 408 | Loading screens (no sensed day yet) |
| 500 | Update failed |

---

## Logging

Pipelines use Python's logging module:

```python
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Log format
fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
```

**Log Levels:**
- INFO: Normal operations, successful saves
- WARNING: Non-critical issues (e.g., no sensed day yet)
- ERROR: Failed operations with stack traces

---

## Usage Examples

### Triggering Profile Update

```python
# From API client
import requests

response = requests.post(
    "https://api.example.com/api/pipelines/create_entire_profile",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "field_id": "1762238407649",
        "farm_email": "john@farm.com",
        "field_name": "North Field",
        "field_area": 5.25,
        "crop": "rice",
        "sowing_date": "2025-10-01",
        "last_sensed_day": "2025-10-29",
        "farm_coordinates": [[15.67844, 77.75649], ...]
    }
)
```

### Direct Function Call

```python
# For testing or batch processing
import asyncio
from pipelines.new_profile_script import update_all_data
from users.models import Farm

farm = Farm.objects.get(field_id="1762238407649")
result = asyncio.run(update_all_data(
    farm=farm,
    field_id="1762238407649",
    crop="rice",
    new_sensed_day="20251029"
))
```

---

## Related Documentation

- [API Reference](./API_REFERENCE.md) - Complete API documentation
- [Integrations](./INTEGRATIONS.md) - External API integration details
- [Heatmaps](./HEATMAPS.md) - Heatmap storage
- [AI Advisory](./AI_ADVISORY.md) - Advisory storage
- [Weather](./WEATHER.md) - Weather storage
- [Crop Loss Analytics](./CROP_LOSS_ANALYTICS.md) - Analytics creation logic
