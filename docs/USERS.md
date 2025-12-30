# Users App Documentation

## Overview

The Users app handles user authentication and farm/field management. It provides endpoints for user registration and farm creation with integration to the Farmanout external API.

## Location

```
src/users/
├── models.py           # User and Farm models
├── api.py              # API endpoints
├── user_schemas.py     # User validation schemas
├── farm_schemas.py     # Farm validation schemas
├── utils.py            # Utility functions
├── admin.py            # Django admin configuration
├── apps.py             # App configuration
├── tests.py            # Test cases
└── migrations/         # Database migrations
```

## Models

### User Model

**File:** `src/users/models.py`

Extends Django's `AbstractUser` for standard authentication.

```python
class User(AbstractUser):
    """Standard Django authentication"""
```

**Fields (inherited from AbstractUser):**

| Field | Type | Description |
|-------|------|-------------|
| id | BigAutoField | Primary key |
| username | CharField | Unique username |
| email | EmailField | User email |
| password | CharField | Hashed password |
| first_name | CharField | First name (optional) |
| last_name | CharField | Last name (optional) |
| is_active | BooleanField | Account active status |
| is_staff | BooleanField | Staff status |
| is_superuser | BooleanField | Superuser status |
| date_joined | DateTimeField | Registration timestamp |
| last_login | DateTimeField | Last login timestamp |

---

### Farm Model

**File:** `src/users/models.py`

Represents a monitored agricultural field.

```python
class Farm(models.Model):
    """Farm/Field information"""
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| id | BigAutoField | Primary key (internal database ID) |
| user | ForeignKey(User) | Owner of the farm (unique constraint) |
| farm_email | EmailField | Contact email for the farm |
| farm_coordinates | JSONField | Polygon coordinates as `[[lat, lon], ...]` |
| field_id | CharField(50) | Unique ID from Farmanout API |
| field_name | CharField(100) | Human-readable field name |
| field_area | DecimalField(10,2) | Area in hectares |
| crop | CharField(50) | Crop type being grown |
| sowing_date | DateField | Date when crop was sown |
| last_sensed_day | DateField | Last satellite observation date (nullable) |
| created_at | DateTimeField | Record creation timestamp |
| updated_at | DateTimeField | Last update timestamp |

**Important Notes:**
- `farm_id` (internal) vs `field_id` (from Farmanout API) - these are different identifiers
- Each user can have only one farm (enforced by `unique=True` on user ForeignKey)
- Coordinates are stored in `[latitude, longitude]` format

**Database Table:** `farms`

**Ordering:** `-created_at` (newest first)

---

## Schemas

### User Schemas

**File:** `src/users/user_schemas.py`

#### CreateUser

Schema for user registration.

```python
class CreateUser(Schema):
    username: str
    email: str
    password: str
```

#### UserSchema

Response schema after user creation.

```python
class UserSchema(Schema):
    id: int
    username: str
    email: str
```

---

### Farm Schemas

**File:** `src/users/farm_schemas.py`

#### FarmCreateSchema

Schema for creating a new farm.

```python
class FarmCreateSchema(Schema):
    farm_email: str
    field_name: str
    crop: str
    sowing_date: date
    farm_coordinates: List[List[float]]  # [[lat, lon], ...]
```

#### FarmResponseSchema

Schema for farm data responses.

```python
class FarmResponseSchema(Schema):
    field_id: str
    farm_email: str
    field_name: str
    field_area: float
    crop: str
    sowing_date: date
    last_sensed_day: Optional[date]
    farm_coordinates: List[List[float]]
```

#### FarmUpdateSchema

Schema for partial farm updates.

```python
class FarmUpdateSchema(Schema):
    field_name: Optional[str] = None
    field_area: Optional[float] = None
    crop: Optional[str] = None
    sowing_date: Optional[date] = None
    last_sensed_day: Optional[date] = None
    farm_coordinates: Optional[List] = None
```

---

## API Endpoints

**Router:** `users_router`
**Base Path:** `/api/users`
**Tags:** `Users`

### Create New User

```
POST /api/users/create_new_user
```

Creates a new user account.

**Authentication:** None required

**Request Body:**
```json
{
  "username": "farmer_john",
  "email": "john@farm.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "id": 1,
  "username": "farmer_john",
  "email": "john@farm.com"
}
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | Username already exists |
| 400 | Email already registered |

---

### Check Registered Farm

```
GET /api/users/already_registered_farm
```

Checks if the authenticated user has a registered farm.

**Authentication:** JWT Required

**Response (200):**
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

| Status | Condition |
|--------|-----------|
| 404 | Farm not found for this user |
| 500 | Database error |

---

### Create New Farm

```
POST /api/users/create_new_farm
```

Creates a new farm for the authenticated user.

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

| Crop Name | Crop Code |
|-----------|-----------|
| rice | 1 |
| turmeric | 21 |
| soyabean | 11 |
| chickpea | 8 |
| red gram | 9 |
| black gram | 45 |
| green gram | 64 |

**Response (200):**
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

**Process Flow:**

1. Check if user already has a farm (returns existing if found)
2. Call Farmanout API to register the field
3. Extract `field_id` and `field_area` from response
4. Get last sensed day from satellite API
5. Create farm record in database
6. Return farm details

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | Unable to add farm via external API |
| 400 | No field_id returned from API |
| 400 | Unable to get last sensed days |
| 400 | Database error during farm creation |

---

## Database Operations

### Creating a User

```python
from django.contrib.auth.hashers import make_password
from users.models import User

user = User.objects.create(
    username="farmer_john",
    email="john@farm.com",
    password=make_password("securepassword123")
)
```

### Creating a Farm

```python
from users.models import Farm

farm = Farm.objects.create(
    user=user,
    farm_email="john@farm.com",
    farm_coordinates=[
        [15.678440, 77.756490],
        [15.678199, 77.757107],
        [15.679233, 77.757575],
        [15.679458, 77.757124],
        [15.679185, 77.756507]
    ],
    field_id="1762238407649",
    field_name="North Field",
    field_area=5.25,
    crop="rice",
    sowing_date="2025-10-01",
    last_sensed_day="2025-10-29"
)
```

### Querying Farms

```python
# Get farm by user
farm = Farm.objects.get(user=user)

# Get farm by field_id
farm = Farm.objects.get(field_id="1762238407649")

# Check if user has a farm
has_farm = Farm.objects.filter(user=user).exists()
```

---

## Related Documentation

- [API Reference](./API_REFERENCE.md) - Complete API documentation
- [Database Structure](./DATABASE.md) - Database schema details
- [Integrations](./INTEGRATIONS.md) - External API integration details
