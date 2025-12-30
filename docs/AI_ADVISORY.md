# AI Advisory App Documentation

## Overview

The AI Advisory app provides AI-powered agricultural recommendations for farms. It stores and retrieves comprehensive advisory data including fertilizer recommendations, irrigation guidance, growth/yield estimation, pest/disease alerts, weed management, and soil management advice.

## Location

```
src/ai_advisory/
├── models.py               # Advisory model
├── api.py                  # API endpoints
├── ai_advisory_schemas.py  # Validation schemas
├── utils.py                # Utility functions for saving data
├── admin.py                # Django admin configuration
├── apps.py                 # App configuration
├── tests.py                # Test cases
└── migrations/             # Database migrations
```

## Models

### Advisory Model

**File:** `src/ai_advisory/models.py`

Stores complete advisory responses from the AI advisory API.

```python
class Advisory(models.Model):
    """Main advisory model storing the complete advisory response"""
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| id | BigAutoField | Primary key |
| farm | ForeignKey(Farm) | Associated farm |
| field_id | CharField(50) | Farmanout field ID (indexed) |
| field_name | CharField(255) | Human-readable field name |
| field_area | DecimalField(10,3) | Field area |
| field_area_unit | CharField(20) | Unit of measurement (default: 'acres') |
| crop | CharField(100) | Crop type |
| sowing_date | DateField | Sowing date |
| timestamp | BigIntegerField | Unix timestamp from API |
| created_at | DateTimeField | Record creation timestamp |
| sar_day | CharField(20) | SAR observation day |
| sensed_day | DateField | Satellite observation date |
| last_satellite_visit | CharField(50) | Last satellite visit info |
| raw_response | JSONField | Complete API response (backup) |
| satellite_data | JSONField | Satellite health summary (green/orange/red/purple/white) |
| advisory_data | JSONField | Parsed advisory recommendations |

**Database Table:** `advisories`

**Constraints:**
- Unique together: `farm`, `sensed_day`

**Indexes:**
- `farm`, `-created_at`
- `field_id`, `-created_at`
- `crop`, `-created_at`

**Ordering:** `-created_at` (newest first)

---

## Advisory Methods

The Advisory model provides methods to extract specific advisory types:

### get_field_metadata()

Returns field metadata in a structured format.

```python
def get_field_metadata(self) -> dict
```

**Returns:**
```json
{
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
}
```

### get_fertilizer_advisory()

Returns fertilizer recommendations.

```python
def get_fertilizer_advisory(self) -> dict
```

**Returns:**
```json
{
  "advisory": {
    "Explanation of calculated parameters": {
      "Fertilizers": ["explanation text..."]
    },
    "Fertilizers": ["fertilizer list..."],
    "Fertilizer": {
      "nitrogen": {"amount": 25, "unit": "kg/ha"},
      "phosphorus": {"amount": 15, "unit": "kg/ha"},
      "potassium": {"amount": 20, "unit": "kg/ha"}
    }
  }
}
```

### get_irrigation_advisory()

Returns irrigation recommendations.

```python
def get_irrigation_advisory(self) -> dict
```

**Returns:**
```json
{
  "advisory": {
    "Explanation of calculated parameters": {
      "Irrigation": ["explanation text..."]
    },
    "Irrigation": {
      "recommended": true,
      "amount": "30mm",
      "frequency": "every 3 days"
    }
  }
}
```

### get_growth_yield_advisory()

Returns growth and yield estimation.

```python
def get_growth_yield_advisory(self) -> dict
```

**Returns:**
```json
{
  "advisory": {
    "Explanation of calculated parameters": {
      "Growth and Yield Estimation": ["explanation text..."]
    },
    "Growth and Yield Estimation": {
      "growth_stage": "vegetative",
      "estimated_yield": "4.5 tons/ha",
      "health_status": "good"
    }
  }
}
```

### get_pest_disease_advisory()

Returns pest and disease alerts.

```python
def get_pest_disease_advisory(self) -> dict
```

**Returns:**
```json
{
  "advisory": {
    "Explanation of calculated parameters": {
      "Pest & Disease": ["explanation text..."]
    },
    "Pest and Disease": {
      "potential_pests": [
        {"name": "stem borer", "probability": "high"},
        {"name": "leaf folder", "probability": "medium"}
      ],
      "preventive_measures": ["measure 1", "measure 2"]
    }
  }
}
```

### get_weed_advisory()

Returns weed management recommendations.

```python
def get_weed_advisory(self) -> dict
```

**Returns:**
```json
{
  "advisory": {
    "Explanation of calculated parameters": {
      "Weed": "explanation text..."
    },
    "Weed": {
      "weed_pressure": "moderate",
      "recommended_action": "manual weeding",
      "herbicide_suggestion": "..."
    }
  }
}
```

### get_soil_management_advisory()

Returns soil management recommendations.

```python
def get_soil_management_advisory(self) -> dict
```

**Returns:**
```json
{
  "advisory": {
    "Explanation of calculated parameters": {
      "Soil Management": ["explanation text..."]
    },
    "Soil Management": {
      "soil_health": "good",
      "organic_matter": "adequate",
      "recommendations": ["recommendation 1", "recommendation 2"]
    }
  }
}
```

---

## Schemas

**File:** `src/ai_advisory/ai_advisory_schemas.py`

### AIAdvisoryItemSchema

Individual advisory item schema.

```python
class AIAdvisoryItemSchema(Schema):
    id: int
    title: str
    description: str
    priority: str
    date: str
```

### AIAdvisoryResponseSchema

List of advisory items.

```python
class AIAdvisoryResponseSchema(Schema):
    advisories: List[AIAdvisoryItemSchema]
```

---

## API Endpoints

**Router:** `ai_advisory_router`
**Base Path:** `/api/ai_advisory`
**Tags:** `ai_advisory`

### Get AI Advisory

```
GET /api/ai_advisory/get_ai_advisory
```

Retrieves comprehensive AI advisory for a specific field and date.

**Authentication:** JWT Required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| field_id | string | Yes | The field_id from Farmanout |
| sensed_date | string | Yes | Date in YYYYMMDD format |

**Example Request:**
```
GET /api/ai_advisory/get_ai_advisory?field_id=1762238407649&sensed_date=20251029
```

**Response (200):**
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
    "advisory": {
      "Explanation of calculated parameters": {
        "Fertilizers": ["Based on current NDVI levels..."]
      },
      "Fertilizers": ["Urea - 25kg/acre", "DAP - 15kg/acre"],
      "Fertilizer": {
        "nitrogen": {"amount": 25, "unit": "kg/ha"}
      }
    }
  },
  "IRRIGATION_ADVISORY": {
    "advisory": {
      "Explanation of calculated parameters": {
        "Irrigation": ["Based on NDMI and RSM indices..."]
      },
      "Irrigation": {
        "recommended": true,
        "amount": "30mm"
      }
    }
  },
  "GROWTH_YIELD_ADVISORY": {
    "advisory": {
      "Explanation of calculated parameters": {
        "Growth and Yield Estimation": ["Based on current growth stage..."]
      },
      "Growth and Yield Estimation": {
        "growth_stage": "vegetative",
        "estimated_yield": "4.5 tons/ha"
      }
    }
  },
  "WEED_ADVISORY": {
    "advisory": {
      "Explanation of calculated parameters": {
        "Weed": "Weed pressure assessment..."
      },
      "Weed": {
        "weed_pressure": "moderate"
      }
    }
  },
  "PEST_DISEASE_ADVISORY": {
    "advisory": {
      "Explanation of calculated parameters": {
        "Pest & Disease": ["Weather conditions favor..."]
      },
      "Pest and Disease": {
        "potential_pests": [
          {"name": "stem borer", "probability": "high"}
        ]
      }
    }
  },
  "SOIL_MANAGEMENT_ADVISORY": {
    "advisory": {
      "Explanation of calculated parameters": {
        "Soil Management": ["Based on SOC levels..."]
      },
      "Soil Management": {
        "soil_health": "good",
        "recommendations": ["Add organic matter"]
      }
    }
  }
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | Farm not found |
| 400 | Invalid date format (expected YYYYMMDD) |
| 404 | No advisory found for this field and date |

---

## Utility Functions

**File:** `src/ai_advisory/utils.py`

### save_ai_adviosry_from_response

Saves advisory data from the external API response.

```python
def save_ai_adviosry_from_response(api_response: dict, field_id: str) -> Advisory
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| api_response | dict | Raw API response from Farmanout |
| field_id | str | The field ID |

**Expected Input Format:**
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

**Returns:** Created Advisory instance

**Behavior:**
- Parses dates from YYYYMMDD format
- Extracts field area from string (handles "5.25 acres" format)
- Stores raw response as backup
- Creates Advisory record with parsed data

---

## Database Operations

### Creating Advisory Records

```python
from ai_advisory.models import Advisory
from users.models import Farm
from datetime import date

farm = Farm.objects.get(field_id="1762238407649")

advisory = Advisory.objects.create(
    farm=farm,
    field_id="1762238407649",
    field_name="North Field",
    field_area=5.25,
    field_area_unit="acres",
    crop="rice",
    sowing_date=date(2025, 10, 1),
    timestamp=1698580800,
    sar_day="Monday",
    sensed_day=date(2025, 10, 29),
    last_satellite_visit="2025-10-29",
    satellite_data={
        "green": "65.5%",
        "orange": "20.3%",
        "red": "5.2%",
        "purple": "4.0%",
        "white": "5.0%"
    },
    advisory_data={
        "Fertilizer": {...},
        "Irrigation": {...}
    },
    raw_response={...}
)
```

### Querying Advisories

```python
# Get advisory for specific farm and date
advisory = Advisory.objects.get(
    farm=farm,
    sensed_day=date(2025, 10, 29)
)

# Get all advisories for a farm
advisories = Advisory.objects.filter(farm=farm).order_by('-sensed_day')

# Get latest advisory
latest = Advisory.objects.filter(farm=farm).first()

# Get advisories with high pest probability
from django.db.models import Q

# Note: This requires checking JSON data
advisories = Advisory.objects.filter(farm=farm)
for adv in advisories:
    pest_data = adv.get_pest_disease_advisory()
    # Check for high probability pests
```

---

## Satellite Data Summary

The `satellite_data` field contains health classification percentages:

| Color | Meaning |
|-------|---------|
| Green | Healthy vegetation |
| Orange | Moderate stress |
| Red | High stress/unhealthy |
| Purple | Very high stress |
| White | No vegetation/bare soil |

---

## Advisory Types Overview

| Type | Description | Key Data |
|------|-------------|----------|
| Fertilizer | Nutrient recommendations | NPK amounts, application timing |
| Irrigation | Water management | Amount, frequency, scheduling |
| Growth & Yield | Crop development status | Growth stage, yield estimate |
| Pest & Disease | Pest alerts and prevention | Pest list, probability, measures |
| Weed | Weed management | Pressure level, control methods |
| Soil Management | Soil health guidance | Organic matter, amendments |

---

## Related Documentation

- [API Reference](./API_REFERENCE.md) - Complete API documentation
- [Database Structure](./DATABASE.md) - Database schema details
- [Integrations](./INTEGRATIONS.md) - External API integration details
- [Pipelines](./PIPELINES.md) - Data processing pipeline details
