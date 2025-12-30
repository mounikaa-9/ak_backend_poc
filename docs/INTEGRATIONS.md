# Integrations Module Documentation

## Overview

The Integrations module handles all external API communications with the Farmanout satellite and agricultural services platform. It provides async HTTP client functions for fetching farm data, satellite imagery, weather forecasts, and AI advisory information.

## Location

```
src/integrations/
├── __init__.py
├── farm_crud_call.py           # Farm creation and boundary editing
├── ai_advisory_crud_call.py    # AI advisory fetching
├── weather_crud_call.py        # Weather forecast fetching
├── heatmaps_crud.py            # Satellite heatmap image fetching
├── index_values_crud_call.py   # Satellite index values fetching
└── get_sensed_days.py          # Last sensed day queries
```

## Common Configuration

All integration functions use the following environment variables:

| Variable | Description |
|----------|-------------|
| `FARMANOUT_API_KEY` | Bearer token for API authentication |
| `SERVER_RESPONSE_TIME` | Timeout in seconds for HTTP requests |

**Headers (common to all calls):**
```python
headers_obj = {
    "Authorization": f"Bearer {os.getenv('FARMANOUT_API_KEY')}",
    "Content-Type": "application/json"
}
```

---

## Farm CRUD Operations

**File:** `src/integrations/farm_crud_call.py`

### add_new_farm

Creates a new farm/field in the Farmanout system.

```python
async def add_new_farm(
    crop_name: str,
    full_name: str,
    date: datetime,
    points: List,  # [[lat, lon], ...]
    payment_type: int = 1
) -> dict
```

**Endpoint:** `POST https://us-central1-farmbase-b2f7e.cloudfunctions.net/submitField`

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| crop_name | str | Crop type (see crop codes) |
| full_name | str | Field name |
| date | datetime | Sowing date (YYYY-MM-DD) |
| points | List | Polygon coordinates [[lat, lon], ...] |
| payment_type | int | Payment type (default: 1) |

**Crop Codes:**

| Crop Name | Code |
|-----------|------|
| rice | 1 |
| turmeric | 21 |
| soyabean | 11 |
| chickpea | 8 |
| red gram | 9 |
| black gram | 45 |
| green gram | 64 |

**Request Body:**
```json
{
  "CropCode": 1,
  "FieldName": "North Field",
  "PaymentType": 1,
  "SowingDate": 1696118400,
  "Points": [[77.756490, 15.678440], [77.757107, 15.678199], ...]
}
```

**Note:** Coordinates are converted from `[lat, lon]` to `[lon, lat]` format for the API.

**Success Response:**
```json
{
  "api": "add_new_farm",
  "field_id": "1762238407649",
  "field_area": 5.25
}
```

**Error Response:**
```json
{
  "api": "add_new_farm",
  "error": "Connection timed out while contacting server"
}
```

---

### edit_field_boundary

Modifies the boundary points of an existing field.

```python
async def edit_field_boundary(field_id: str, points: List) -> dict
```

**Endpoint:** `POST https://us-central1-farmbase-b2f7e.cloudfunctions.net/modifyFieldPoints`

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| field_id | str | Farmanout field ID |
| points | List | New polygon coordinates [[lat, lon], ...] |

**Request Body:**
```json
{
  "FieldID": "1762238407649",
  "Points": [[77.756490, 15.678440], [77.757107, 15.678199], ...]
}
```

**Success Response:**
```json
{
  "api": "edit_field_boundary",
  "last_sensed_day": "20251029"
}
```

---

### latlong_to_longlat

Helper function to convert coordinate format.

```python
def latlong_to_longlat(points: List) -> List
```

Converts `[[lat, lon], ...]` to `[[lon, lat], ...]` for API compatibility.

---

## AI Advisory

**File:** `src/integrations/ai_advisory_crud_call.py`

### get_ai_advisory

Fetches comprehensive AI agricultural advisory for a field.

```python
async def get_ai_advisory(field_id: str, crop: str) -> dict
```

**Endpoint:** `POST https://us-central1-farmbase-b2f7e.cloudfunctions.net/askJeevnAPI`

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| field_id | str | Farmanout field ID |
| crop | str | Crop type |

**Request Body:**
```json
{
  "Crop": "rice",
  "FieldID": "1762238407649"
}
```

**Timeout:** 3x `SERVER_RESPONSE_TIME` (longer timeout for AI processing)

**Success Response:**
```json
{
  "fieldID": "1762238407649",
  "fieldName": "North Field",
  "fieldArea": "5.25 acres",
  "Crop": "rice",
  "SowingDate": "20251001",
  "SensedDay": "20251029",
  "SARDay": "Monday",
  "lastSatelliteVisit": "2025-10-29",
  "timestamp": 1698580800,
  "Satellite_Data": {
    "green": "65.5%",
    "orange": "20.3%",
    "red": "5.2%",
    "purple": "4.0%",
    "white": "5.0%"
  },
  "advisory": {
    "Fertilizer": {...},
    "Irrigation": {...},
    "Growth and Yield Estimation": {...},
    "Pest and Disease": {...},
    "Weed": {...},
    "Soil Management": {...},
    "Explanation of calculated parameters": {...}
  }
}
```

---

## Weather Forecast

**File:** `src/integrations/weather_crud_call.py`

### weather_forecast

Fetches weather forecast for a field's location.

```python
async def weather_forecast(field_id: str) -> dict
```

**Endpoint:** `POST https://us-central1-farmbase-b2f7e.cloudfunctions.net/getPresentWeather`

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| field_id | str | Farmanout field ID |

**Request Body:**
```json
{
  "FieldID": "1762238407649"
}
```

**Success Response:**
```json
{
  "api": "weather_forecast",
  "weather": {
    "daily": [
      {
        "dt": 1698580800,
        "summary": "Clear sky",
        "weather": [{"description": "clear sky", "main": "Clear", "icon": "01d"}],
        "temp": {"day": 32.5, "min": 24.2, "max": 34.8, ...},
        "feels_like": {"day": 34.2, ...},
        "humidity": 65,
        "pressure": 1012,
        "wind_speed": 3.2,
        "rain": 0,
        ...
      },
      ...
    ]
  }
}
```

---

## Heatmap Images

**File:** `src/integrations/heatmaps_crud.py`

### get_field_image

Fetches a single satellite heatmap image URL.

```python
async def get_field_image(
    field_id: str,
    sensed_day: str,
    image_type: str
) -> dict
```

**Endpoint:** `POST https://us-central1-farmbase-b2f7e.cloudfunctions.net/getFieldImage`

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| field_id | str | Farmanout field ID |
| sensed_day | str | Date in YYYYMMDD format |
| image_type | str | Image type code (see below) |

**Request Body:**
```json
{
  "FieldID": "1762238407649",
  "ImageType": "ndvi",
  "SensedDay": "20251029"
}
```

**Success Response:**
```json
{
  "api": "get_field_image",
  "image_type": "ndvi",
  "url": "https://storage.googleapis.com/..."
}
```

---

### get_all_images

Fetches all available satellite image types for a field.

```python
async def get_all_images(field_id: str, sensed_day: str) -> dict
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| field_id | str | Farmanout field ID |
| sensed_day | str | Date in YYYYMMDD format |

**Available Image Types:**

| Code | Description |
|------|-------------|
| ndvi | Normalized Difference Vegetation Index |
| ndwi | Normalized Difference Water Index |
| evapo | Evapotranspiration |
| ndmi | Normalized Difference Moisture Index |
| evi | Enhanced Vegetation Index |
| rvi | Ratio Vegetation Index |
| rsm | Root Zone Soil Moisture |
| ndre | Normalized Difference Red Edge |
| vari | Visible Atmospherically Resistant Index |
| savi | Soil Adjusted Vegetation Index |
| avi | Advanced Vegetation Index |
| bsi | Bare Soil Index |
| si | Salinity Index |
| soc | Soil Organic Carbon |
| tci | Temperature Condition Index |
| etci | ETCI Index |
| hybrid | Combined multi-index view |
| hybrid_blind | Colorblind-friendly combined view |
| dem | Digital Elevation Model |
| lulc | Land Use Land Cover |

**Success Response:**
```json
{
  "ndvi": "https://storage.googleapis.com/.../ndvi.png",
  "savi": "https://storage.googleapis.com/.../savi.png",
  "evi": "https://storage.googleapis.com/.../evi.png",
  "...": "...",
  "_meta": {
    "field_id": "1762238407649",
    "sensed_day": "20251029",
    "timestamp": "2025-10-29T10:30:00"
  }
}
```

**Note:** All image requests are made concurrently using `asyncio.gather()` for performance.

---

## Index Values

**File:** `src/integrations/index_values_crud_call.py`

### get_index_values

Fetches numerical satellite index values for a specific date.

```python
async def get_index_values(field_id: str, sensed_day: str) -> dict
```

**Endpoint:** `POST https://us-central1-farmbase-b2f7e.cloudfunctions.net/getAllIndexValues`

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| field_id | str | Farmanout field ID |
| sensed_day | str | Date in YYYYMMDD format |

**Request Body:**
```json
{
  "FieldID": "1762238407649"
}
```

**Success Response:**
```json
{
  "api": "get_index_values",
  "rvi": 1.25,
  "ndvi": 0.65,
  "savi": 0.48,
  "evi": 0.52,
  "ndre": 0.35,
  "rsm": 45.2,
  "ndwi": -0.12,
  "ndmi": 0.28,
  "evapo": 3.5,
  "soc": 2.1,
  "etci": 0.75,
  "_meta": {
    "field_id": "1762238407649",
    "sensed_day": "20251029"
  }
}
```

**Note:** A value of `-1` indicates missing/unavailable data for that index.

---

## Sensed Days

**File:** `src/integrations/get_sensed_days.py`

### get_sensed_days

Fetches the last satellite observation date for a field.

```python
async def get_sensed_days(field_id: str) -> dict
```

**Endpoint:** `POST https://us-central1-farmbase-b2f7e.cloudfunctions.net/getSensedDays`

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| field_id | str | Farmanout field ID |

**Request Body:**
```json
{
  "FieldID": "1762238407649"
}
```

**Success Response:**
```json
{
  "api": "get_sensed_days",
  "last_sensed_day": "20251029"
}
```

**Process:**
- API returns all sensed days as keys in the response
- Function finds the maximum (most recent) date
- Returns in YYYYMMDD format

---

## Error Handling

All integration functions handle the following error types:

| Error Type | Description |
|------------|-------------|
| `httpx.ConnectTimeout` | Connection timed out |
| `httpx.ReadTimeout` | Server took too long to respond |
| `httpx.ConnectError` | Failed to connect (network/URL issue) |
| `httpx.HTTPStatusError` | HTTP 4xx/5xx error |
| `json.JSONDecodeError` | Invalid JSON response |

**Error Response Format:**
```json
{
  "api": "function_name",
  "error": "Error description",
  "details": "Additional error details (optional)"
}
```

---

## Usage Examples

### Fetching Farm Data

```python
import asyncio
from integrations.farm_crud_call import add_new_farm
from integrations.get_sensed_days import get_sensed_days

# Create a new farm
result = asyncio.run(add_new_farm(
    crop_name="rice",
    full_name="North Field",
    date="2025-10-01",
    points=[
        [15.678440, 77.756490],
        [15.678199, 77.757107],
        [15.679233, 77.757575],
        [15.679458, 77.757124],
        [15.679185, 77.756507]
    ]
))

# Get last sensed day
sensed = asyncio.run(get_sensed_days(field_id=result["field_id"]))
```

### Fetching Satellite Data

```python
from integrations.heatmaps_crud import get_all_images
from integrations.index_values_crud_call import get_index_values

# Fetch all images
images = asyncio.run(get_all_images(
    field_id="1762238407649",
    sensed_day="20251029"
))

# Fetch index values
indices = asyncio.run(get_index_values(
    field_id="1762238407649",
    sensed_day="20251029"
))
```

### Fetching Advisory and Weather

```python
from integrations.ai_advisory_crud_call import get_ai_advisory
from integrations.weather_crud_call import weather_forecast

# Fetch AI advisory
advisory = asyncio.run(get_ai_advisory(
    field_id="1762238407649",
    crop="rice"
))

# Fetch weather
weather = asyncio.run(weather_forecast(
    field_id="1762238407649"
))
```

---

## API Endpoints Summary

| Function | Endpoint | Method |
|----------|----------|--------|
| add_new_farm | /submitField | POST |
| edit_field_boundary | /modifyFieldPoints | POST |
| get_ai_advisory | /askJeevnAPI | POST |
| weather_forecast | /getPresentWeather | POST |
| get_field_image | /getFieldImage | POST |
| get_index_values | /getAllIndexValues | POST |
| get_sensed_days | /getSensedDays | POST |

**Base URL:** `https://us-central1-farmbase-b2f7e.cloudfunctions.net`

---

## Related Documentation

- [API Reference](./API_REFERENCE.md) - Complete API documentation
- [Pipelines](./PIPELINES.md) - How integrations are used in data processing
- [Users](./USERS.md) - Farm creation flow
- [Heatmaps](./HEATMAPS.md) - Image storage
- [AI Advisory](./AI_ADVISORY.md) - Advisory storage
- [Weather](./WEATHER.md) - Weather storage
