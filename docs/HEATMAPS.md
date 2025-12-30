# Heatmaps App Documentation

## Overview

The Heatmaps app manages satellite imagery heatmaps and vegetation index time-series data. It provides storage and retrieval of satellite-based agricultural monitoring data, with images stored in Azure Blob Storage.

## Location

```
src/heatmaps/
├── models.py               # IndexTimeSeries and Heatmap models
├── api.py                  # API endpoints
├── heatmap_schemas.py      # Heatmap validation schemas
├── time_series_schemas.py  # Time series validation schemas
├── utils.py                # Utility functions for saving data
├── admin.py                # Django admin configuration
├── apps.py                 # App configuration
├── tests.py                # Test cases
└── migrations/             # Database migrations
```

## Models

### IndexTimeSeries Model

**File:** `src/heatmaps/models.py`

Stores numerical time-series data for satellite vegetation indices.

```python
class IndexTimeSeries(models.Model):
    """Time series data for various satellite values"""
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| id | BigAutoField | Primary key |
| farm | ForeignKey(Farm) | Associated farm |
| index_type | CharField(10) | Type of index (see INDEX_CHOICES) |
| date | DateField | Date of satellite observation |
| value | DecimalField(6,2) | Index value (nullable) |
| created_at | DateTimeField | Record creation timestamp |

**INDEX_CHOICES:**

| Code | Full Name | Description |
|------|-----------|-------------|
| `rvi` | RVI - Ratio Vegetation Index | Basic vegetation ratio |
| `ndvi` | NDVI - Normalized Difference Vegetation Index | Overall vegetation health |
| `savi` | SAVI - Soil Adjusted Vegetation Index | Vegetation in sparse/exposed soil areas |
| `evi` | EVI - Enhanced Vegetation Index | Dense vegetation monitoring |
| `ndre` | NDRE - Normalized Difference Red Edge | Chlorophyll/nitrogen content |
| `rsm` | RSM - Root Zone Soil Moisture | Soil moisture at root level |
| `ndwi` | NDWI - Normalized Difference Water Index | Surface water content |
| `ndmi` | NDMI - Normalized Difference Moisture Index | Vegetation moisture stress |
| `evapo` | ET - Evapotranspiration | Water loss from soil/plants |
| `soc` | SOC - Soil Organic Carbon | Soil health indicator |
| `etci` | ETCI | Combined thermal/vegetation index |

**Database Table:** `index_time_series`

**Constraints:**
- Unique together: `farm`, `index_type`, `date`

**Ordering:** `date` (ascending)

---

### Heatmap Model

**File:** `src/heatmaps/models.py`

Stores URLs for satellite heatmap images in Azure Blob Storage.

```python
class Heatmap(models.Model):
    """Heatmap images storage"""
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| id | BigAutoField | Primary key |
| farm | ForeignKey(Farm) | Associated farm |
| index_type | CharField(10) | Type of index (see INDEX_CHOICES) |
| date | DateField | Date of satellite observation |
| image_url | URLField(500) | Azure Blob Storage URL (nullable) |
| created_at | DateTimeField | Record creation timestamp |

**INDEX_CHOICES:**

All IndexTimeSeries types plus:

| Code | Full Name | Description |
|------|-----------|-------------|
| `hybrid` | HYBRID | Combined multi-index visualization |

**Database Table:** `heatmaps`

**Constraints:**
- Unique together: `farm`, `index_type`, `date`

---

## Schemas

### Heatmap Schemas

**File:** `src/heatmaps/heatmap_schemas.py`

#### HeatmapSchema

Response schema for heatmap data.

```python
class HeatmapSchema(Schema):
    farm_id: str
    index_type: str
    date: date
    image_url: Optional[str]
```

#### HeatmapCreateSchema

Schema for creating heatmap records.

```python
class HeatmapCreateSchema(Schema):
    farm_id: str
    index_type: str
    date: date
    image_url: Optional[str]
```

#### HeatmapURLSchema

Schema for requesting heatmap URLs.

```python
class HeatmapURLSchema(Schema):
    farm_id: str
    index_type: str
    sensed_day: date
```

#### HeatmapListSchema

Schema for returning multiple heatmaps.

```python
class HeatmapListSchema(Schema):
    heatmaps: List[HeatmapSchema]
```

---

### Time Series Schemas

**File:** `src/heatmaps/time_series_schemas.py`

#### IndexTimeSeriesSchema

Full time series record schema.

```python
class IndexTimeSeriesSchema(Schema):
    id: int
    farm_id: str
    index_type: str
    date: date
    value: Optional[Decimal]
```

#### IndexValueDateSchema

Simple date-value pair.

```python
class IndexValueDateSchema(Schema):
    date: date
    value: Optional[Decimal]
```

#### IndexValueDateResponseSchema

Single value response.

```python
class IndexValueDateResponseSchema(Schema):
    value: Optional[Decimal]
```

#### IndexTimeSeriesResponseSchema

Time series data response.

```python
class IndexTimeSeriesResponseSchema(Schema):
    farm_id: str
    index_type: str
    data: List[IndexValueDateSchema]
```

---

## API Endpoints

**Router:** `heatmaps_router`
**Base Path:** `/api/heatmaps`
**Tags:** `heatmaps`, `satellite-specific-time-series`

### Get Heatmap URL

```
GET /api/heatmaps/get_heatmaps
```

Retrieves a heatmap image URL with a secure SAS token.

**Authentication:** JWT Required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| farm_id | string | Yes | The field_id from Farmanout |
| index_type | string | Yes | Index type (ndvi, savi, etc.) |
| sensed_date | string | Yes | Date in YYYYMMDD format |

**Example Request:**
```
GET /api/heatmaps/get_heatmaps?farm_id=1762238407649&index_type=ndvi&sensed_date=20251029
```

**Response (200):**
```json
{
  "farm_id": "1762238407649",
  "index_type": "ndvi",
  "date": "2025-10-29",
  "image_url": "https://account.blob.core.windows.net/container/path/ndvi.png?sv=2021-06-08&se=2025-10-29T12:00:00Z&sr=b&sp=r&sig=...",
  "expires_at": "2025-10-29T12:00:00Z"
}
```

**SAS Token Details:**
- Valid for 60 minutes
- Read-only permission
- Start time offset by 5 minutes to handle clock skew

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | Farm not found |
| 400 | Invalid date format |
| 400 | Heatmap not found |
| 404 | Heatmap image not found in storage |
| 500 | Failed to generate access URL |

---

### Get Past Satellite Values

```
GET /api/heatmaps/get_past_satellite_values
```

Retrieves satellite index values for the last 30 days.

**Authentication:** None required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| farm_id | string | Yes | The field_id from Farmanout |
| index_type | string | Yes | Index type (ndvi, savi, etc.) |

**Example Request:**
```
GET /api/heatmaps/get_past_satellite_values?farm_id=1762238407649&index_type=ndvi
```

**Response (200):**
```json
{
  "farm_id": "1762238407649",
  "index_type": "ndvi",
  "data": [
    {"date": "2025-10-01", "value": 0.45},
    {"date": "2025-10-08", "value": 0.52},
    {"date": "2025-10-15", "value": 0.58},
    {"date": "2025-10-22", "value": 0.61},
    {"date": "2025-10-29", "value": 0.65}
  ]
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | Farm not found |

---

### Get Single Past Satellite Value

```
GET /api/heatmaps/get_one_past_satellite_value
```

Retrieves a single satellite index value for a specific date.

**Authentication:** None required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| farm_id | string | Yes | The field_id from Farmanout |
| index_type | string | Yes | Index type (ndvi, savi, etc.) |
| date | string | Yes | Date (YYYY-MM-DD format) |

**Example Request:**
```
GET /api/heatmaps/get_one_past_satellite_value?farm_id=1762238407649&index_type=ndvi&date=2025-10-29
```

**Response (200):**
```json
{
  "value": 0.65
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | Farm not found |

---

## Utility Functions

**File:** `src/heatmaps/utils.py`

### save_heatmaps_from_response

Saves satellite index image URLs to the Heatmap model.

```python
def save_heatmaps_from_response(field_data: dict)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| field_data | dict | JSON response containing URLs and metadata |

**Expected Input Format:**
```json
{
  "_meta": {
    "field_id": "1762238407649",
    "sensed_day": "20251029",
    "timestamp": "2025-10-29T10:30:00"
  },
  "ndvi": "https://azure.blob.core.windows.net/.../ndvi.png",
  "savi": "https://azure.blob.core.windows.net/.../savi.png",
  "evi": "https://azure.blob.core.windows.net/.../evi.png"
}
```

**Behavior:**
- Parses `sensed_day` from YYYYMMDD format
- Uses atomic transaction for data integrity
- Uses `update_or_create` to handle duplicates
- Skips unrecognized index types silently

---

### save_index_values_from_response

Saves satellite index numerical values to the IndexTimeSeries model.

```python
def save_index_values_from_response(field_data: dict)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| field_data | dict | JSON response containing index values and metadata |

**Expected Input Format:**
```json
{
  "_meta": {
    "field_id": "1762238407649",
    "sensed_day": "20251029"
  },
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
  "etci": 0.75
}
```

**Behavior:**
- Converts `-1` values to `NULL` in database
- Uses atomic transaction for data integrity
- Uses `update_or_create` to handle duplicates
- Skips unrecognized index types silently

---

## SAS URL Generation

**File:** `src/heatmaps/api.py`

### generate_sas_url

Generates a secure SAS (Shared Access Signature) URL for Azure Blob Storage.

```python
def generate_sas_url(blob_url: str, expiry_minutes: int = 60) -> str
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| blob_url | string | - | Full Azure blob URL |
| expiry_minutes | int | 60 | Token validity duration |

**Returns:** Blob URL with SAS token appended

**Process:**
1. Parse blob URL to extract container and blob names
2. Extract account credentials from connection string
3. Verify blob exists in storage
4. Generate SAS token with read permission
5. Return URL with token appended

---

## Database Operations

### Creating Index Time Series

```python
from heatmaps.models import IndexTimeSeries
from users.models import Farm

farm = Farm.objects.get(field_id="1762238407649")

IndexTimeSeries.objects.create(
    farm=farm,
    index_type="ndvi",
    date="2025-10-29",
    value=0.65
)
```

### Creating Heatmap Records

```python
from heatmaps.models import Heatmap

Heatmap.objects.create(
    farm=farm,
    index_type="ndvi",
    date="2025-10-29",
    image_url="https://account.blob.core.windows.net/container/path/ndvi.png"
)
```

### Querying Time Series Data

```python
from datetime import date, timedelta

# Get last 30 days of NDVI values
thirty_days_ago = date.today() - timedelta(days=30)

values = IndexTimeSeries.objects.filter(
    farm=farm,
    index_type="ndvi",
    date__gte=thirty_days_ago
).order_by("date").values("date", "value")
```

### Querying Heatmaps

```python
# Get specific heatmap
heatmap = Heatmap.objects.filter(
    farm=farm,
    index_type="ndvi",
    date="2025-10-29"
).first()

# Get all heatmaps for a farm
heatmaps = Heatmap.objects.filter(farm=farm).order_by("-date")
```

---

## Image Types Available

The system retrieves and stores the following image types from the satellite API:

| Code | Description | Stored in Heatmap |
|------|-------------|-------------------|
| ndvi | Vegetation Index | Yes |
| ndwi | Water Index | Yes |
| evapo | Evapotranspiration | Yes |
| ndmi | Moisture Index | Yes |
| evi | Enhanced Vegetation | Yes |
| rvi | Ratio Vegetation | Yes |
| rsm | Root Soil Moisture | Yes |
| ndre | Red Edge | Yes |
| savi | Soil Adjusted VI | Yes |
| soc | Soil Organic Carbon | Yes |
| etci | ETCI Index | Yes |
| hybrid | Combined View | Yes |
| vari | VARI Index | No (not in choices) |
| avi | AVI Index | No (not in choices) |
| bsi | Bare Soil Index | No (not in choices) |
| si | SI Index | No (not in choices) |
| tci | TCI Index | No (not in choices) |
| hybrid_blind | Colorblind View | No (not in choices) |
| dem | Digital Elevation | No (not in choices) |
| lulc | Land Use/Cover | No (not in choices) |

---

## Related Documentation

- [API Reference](./API_REFERENCE.md) - Complete API documentation
- [Database Structure](./DATABASE.md) - Database schema details
- [Integrations](./INTEGRATIONS.md) - External API integration details
- [Pipelines](./PIPELINES.md) - Data processing pipeline details
