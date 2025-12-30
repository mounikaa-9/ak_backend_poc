# API Reference

## Overview

The AK Backend POC API is built using Django Ninja, providing a fast, type-safe REST API with automatic OpenAPI documentation.

## Base URL

- **Local Development:** `http://localhost:8000/api/`
- **Production:** `https://your-app.vercel.app/api/`

## Authentication

The API uses JWT (JSON Web Token) authentication.

### Obtaining Tokens

```
POST /api/auth/token/pair
```

**Request Body:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Refreshing Tokens

```
POST /api/auth/token/refresh
```

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Using Tokens

Include the access token in the `Authorization` header:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Token Lifetimes

| Token | Lifetime |
|-------|----------|
| Access Token | 60 minutes |
| Refresh Token | 7 days |

---

## API Endpoints Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/auth/token/pair` | POST | No | Obtain JWT tokens |
| `/api/auth/token/refresh` | POST | No | Refresh access token |
| `/api/users/create_new_user` | POST | No | Create new user |
| `/api/users/already_registered_farm` | GET | JWT | Get user's farm |
| `/api/users/create_new_farm` | POST | JWT | Create new farm |
| `/api/heatmaps/get_heatmaps` | GET | JWT | Get heatmap URL |
| `/api/heatmaps/get_past_satellite_values` | GET | No | Get satellite time series |
| `/api/heatmaps/get_one_past_satellite_value` | GET | No | Get single satellite value |
| `/api/ai_advisory/get_ai_advisory` | GET | JWT | Get AI advisory |
| `/api/weather/get_weather` | GET | JWT | Get weather forecast |
| `/api/crop_loss_analytics/crop_loss_analytics` | GET | JWT | Get crop loss status |
| `/api/pipelines/create_entire_profile` | POST | JWT | Full profile update |
| `/api/pipelines/sync/sync_create_entire_profile` | POST | JWT | Sync profile update |

---

## Users API

### Create New User

Creates a new user account.

```
POST /api/users/create_new_user
```

**Authentication:** None

**Request Body:**
```json
{
  "username": "farmer_john",
  "email": "john@farm.com",
  "password": "securepassword123"
}
```

**Success Response (200):**
```json
{
  "id": 1,
  "username": "farmer_john",
  "email": "john@farm.com"
}
```

**Error Responses:**
- `400` - Username already exists
- `400` - Email already registered

---

### Get Registered Farm

Checks if the authenticated user has a registered farm.

```
GET /api/users/already_registered_farm
```

**Authentication:** JWT Required

**Success Response (200):**
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
    [15.678199, 77.757107],
    [15.679233, 77.757575],
    [15.679458, 77.757124],
    [15.679185, 77.756507]
  ]
}
```

**Error Responses:**
- `404` - Farm not found for this user
- `500` - Database error

---

### Create New Farm

Creates a new farm for the authenticated user.

```
POST /api/users/create_new_farm
```

**Authentication:** JWT Required

**Request Body:**
```json
{
  "farm_email": "john@farm.com",
  "field_name": "North Field",
  "crop": "rice",
  "sowing_date": "2025-10-01",
  "farm_coordinates": [
    [15.678440, 77.756490],
    [15.678199, 77.757107],
    [15.679233, 77.757575],
    [15.679458, 77.757124],
    [15.679185, 77.756507]
  ]
}
```

**Supported Crops:**
- rice
- turmeric
- soyabean
- chickpea
- red gram
- black gram
- green gram

**Success Response (200):**
```json
{
  "field_id": "1762238407649",
  "farm_email": "john@farm.com",
  "field_name": "North Field",
  "field_area": 5.25,
  "crop": "rice",
  "sowing_date": "2025-10-01",
  "last_sensed_day": "2025-10-29",
  "farm_coordinates": [...]
}
```

**Error Responses:**
- `400` - Unable to add farm via external API
- `400` - No field_id returned
- `400` - Database error

---

## Heatmaps API

### Get Heatmap URL

Retrieves a heatmap image URL with secure SAS token.

```
GET /api/heatmaps/get_heatmaps
```

**Authentication:** JWT Required

**Query Parameters:**

| Parameter | Type | Required | Example | Description |
|-----------|------|----------|---------|-------------|
| farm_id | string | Yes | 1762238407649 | Farmanout field ID |
| index_type | string | Yes | ndvi | Index type code |
| sensed_date | string | Yes | 20251029 | Date (YYYYMMDD) |

**Success Response (200):**
```json
{
  "farm_id": "1762238407649",
  "index_type": "ndvi",
  "date": "2025-10-29",
  "image_url": "https://account.blob.core.windows.net/container/path/ndvi.png?sv=2021-06-08&se=...",
  "expires_at": "2025-10-29T12:00:00Z"
}
```

**Available Index Types:**
- ndvi, savi, evi, ndre, rsm, ndwi, ndmi, evapo, soc, etci, rvi, hybrid

**Error Responses:**
- `400` - Farm not found
- `400` - Invalid date format
- `400` - Heatmap not found
- `404` - Image not found in storage
- `500` - Failed to generate access URL

---

### Get Past Satellite Values

Retrieves satellite index values for the last 30 days.

```
GET /api/heatmaps/get_past_satellite_values
```

**Authentication:** None

**Query Parameters:**

| Parameter | Type | Required | Example | Description |
|-----------|------|----------|---------|-------------|
| farm_id | string | Yes | 1762238407649 | Farmanout field ID |
| index_type | string | Yes | ndvi | Index type code |

**Success Response (200):**
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
- `400` - Farm not found

---

### Get Single Satellite Value

Retrieves a single satellite index value for a specific date.

```
GET /api/heatmaps/get_one_past_satellite_value
```

**Authentication:** None

**Query Parameters:**

| Parameter | Type | Required | Example | Description |
|-----------|------|----------|---------|-------------|
| farm_id | string | Yes | 1762238407649 | Farmanout field ID |
| index_type | string | Yes | ndvi | Index type code |
| date | string | Yes | 2025-10-29 | Date (YYYY-MM-DD) |

**Success Response (200):**
```json
{
  "value": 0.65
}
```

**Error Responses:**
- `400` - Farm not found

---

## AI Advisory API

### Get AI Advisory

Retrieves comprehensive AI advisory for a specific field and date.

```
GET /api/ai_advisory/get_ai_advisory
```

**Authentication:** JWT Required

**Query Parameters:**

| Parameter | Type | Required | Example | Description |
|-----------|------|----------|---------|-------------|
| field_id | string | Yes | 1762238407649 | Farmanout field ID |
| sensed_date | string | Yes | 20251029 | Date (YYYYMMDD) |

**Success Response (200):**
```json
{
  "FIELD_METADATA": {
    "crop": "rice",
    "fieldName": "North Field",
    "fieldArea": "5.25 acres",
    "sowingDate": "2025-10-01",
    "sarDay": "Monday",
    "lastSatelliteVisit": "2025-10-29",
    "fieldId": "1762238407649",
    "sensedDay": "2025-10-29",
    "generatedOn": 1698580800,
    "satelliteDataSummary": {
      "green": 65.5,
      "orange": 20.3,
      "red": 5.2,
      "purple": 4.0,
      "white": 5.0
    }
  },
  "FERTILIZER_ADVISORY": {
    "advisory": {...}
  },
  "IRRIGATION_ADVISORY": {
    "advisory": {...}
  },
  "GROWTH_YIELD_ADVISORY": {
    "advisory": {...}
  },
  "WEED_ADVISORY": {
    "advisory": {...}
  },
  "PEST_DISEASE_ADVISORY": {
    "advisory": {...}
  },
  "SOIL_MANAGEMENT_ADVISORY": {
    "advisory": {...}
  }
}
```

**Error Responses:**
- `400` - Farm not found
- `400` - Invalid date format
- `404` - No advisory found for this field and date

---

## Weather API

### Get Weather

Retrieves weather predictions for a specific farm and date.

```
GET /api/weather/get_weather
```

**Authentication:** JWT Required

**Query Parameters:**

| Parameter | Type | Required | Example | Description |
|-----------|------|----------|---------|-------------|
| field_id | string | Yes | 1762238407649 | Farmanout field ID |
| current_date | string | Yes | 20251029 | Date (YYYYMMDD) |

**Success Response (200):**
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
    "...": "..."
  }
]
```

**Error Responses:**
- `400` - Farm not found
- `400` - Invalid date format
- `404` - No weather data found for this date

---

## Crop Loss Analytics API

### Get Crop Loss Analytics

Retrieves active crop loss analytics for a specific scenario type.

```
GET /api/crop_loss_analytics/crop_loss_analytics
```

**Authentication:** JWT Required

**Query Parameters:**

| Parameter | Type | Required | Values | Description |
|-----------|------|----------|--------|-------------|
| kind | string | Yes | flood, pest, drought | Scenario type |

**Success Response (200) - Active scenario:**
```json
{
  "start_date": "2025-10-25",
  "approx_end_date": "2025-10-29",
  "kind": "flood"
}
```

**Success Response (200) - No active scenario:**
```json
{
  "start_date": null,
  "approx_end_date": null,
  "kind": "flood"
}
```

**Error Responses:**
- `400` - Farm not found

---

## Pipelines API

### Create Entire Profile (Async)

Full asynchronous profile update with concurrent operations.

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

**Success Response (200) - Full Update:**
```json
{
  "status": "success",
  "field_id": "1762238407649",
  "last_sensed_day": "20251029",
  "update_type": "full"
}
```

**Success Response (200) - Weather Only:**
```json
{
  "status": "success",
  "field_id": "1762238407649",
  "last_sensed_day": "20251029",
  "update_type": "weather_only"
}
```

**Error Responses:**
- `404` - Farm not found
- `408` - Currently loading screens (no sensed day)
- `500` - Update failed

---

### Sync Create Entire Profile

Synchronous profile update with detailed status tracking.

```
POST /api/pipelines/sync/sync_create_entire_profile
```

**Authentication:** JWT Required

**Request Body:** Same as async endpoint

**Success Response (200):**
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

**Error Responses:** Same as async endpoint

---

## Error Response Format

All API errors follow this format:

```json
{
  "detail": "Error message describing the issue"
}
```

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing or invalid token |
| 404 | Not Found - Resource doesn't exist |
| 408 | Request Timeout - Data not ready |
| 500 | Internal Server Error |

---

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting for production use.

---

## OpenAPI Documentation

When running locally, automatic API documentation is available at:

- **Swagger UI:** `http://localhost:8000/api/docs`
- **OpenAPI Schema:** `http://localhost:8000/api/openapi.json`

---

## Related Documentation

- [Users](./USERS.md) - User and Farm endpoints
- [Heatmaps](./HEATMAPS.md) - Satellite data endpoints
- [AI Advisory](./AI_ADVISORY.md) - Advisory endpoints
- [Weather](./WEATHER.md) - Weather endpoints
- [Crop Loss Analytics](./CROP_LOSS_ANALYTICS.md) - Analytics endpoints
- [Pipelines](./PIPELINES.md) - Pipeline endpoints
