# AK Backend POC Documentation

## Overview

AK Backend POC is a Django-based backend for an agricultural monitoring and advisory system. It integrates satellite imagery, weather forecasting, AI-driven agricultural advisory, and crop loss analytics for farm field monitoring.

## Technology Stack

| Component | Technology |
|-----------|------------|
| Framework | Django 5.2.7 |
| API Framework | Django Ninja 1.1.0 + Ninja Extra 0.20.7 |
| Authentication | JWT (ninja-jwt 5.3.1) |
| Database | PostgreSQL |
| Cloud Storage | Azure Blob Storage |
| HTTP Client | HTTPX (async) |
| Geospatial | Shapely 2.1.1 |

## Project Structure

```
ak_backend_poc/
├── src/                          # Main application directory
│   ├── ak_backend_poc/           # Django project configuration
│   │   ├── settings.py           # Django settings
│   │   ├── urls.py               # URL routing
│   │   ├── api.py                # API router registration
│   │   ├── wsgi.py               # WSGI entry point
│   │   └── asgi.py               # ASGI entry point
│   │
│   ├── users/                    # User and Farm management
│   ├── heatmaps/                 # Satellite heatmaps and index values
│   ├── ai_advisory/              # AI-powered agricultural advisory
│   ├── weather/                  # Weather forecasting
│   ├── crop_loss_analytics/      # Crop loss tracking
│   ├── integrations/             # External API integrations
│   ├── pipelines/                # Data processing pipelines
│   └── utils/                    # Utility functions
│
├── docs/                         # Documentation (this folder)
├── requirements.txt              # Python dependencies
├── vercel.json                   # Vercel deployment config
├── railway.toml                  # Railway deployment config
└── DockerFile                    # Docker configuration
```

## Documentation Index

| Document | Description |
|----------|-------------|
| [API Reference](./API_REFERENCE.md) | Complete API endpoints documentation |
| [Database Structure](./DATABASE.md) | Database models and relationships |
| [Users App](./USERS.md) | User and Farm management |
| [Heatmaps App](./HEATMAPS.md) | Satellite imagery and indices |
| [AI Advisory App](./AI_ADVISORY.md) | Agricultural advisory system |
| [Weather App](./WEATHER.md) | Weather forecasting |
| [Crop Loss Analytics](./CROP_LOSS_ANALYTICS.md) | Crop loss tracking |
| [Integrations](./INTEGRATIONS.md) | External API integrations |
| [Pipelines](./PIPELINES.md) | Data processing pipelines |

## Quick Start

### Environment Variables

Create a `.env` file with the following variables:

```env
SECRET_KEY=your-django-secret-key
DEBUG=1
DATABASE_URL=postgresql://user:password@host:port/dbname
AZURE_CONNECTION_STRING=your-azure-connection-string
FARMANOUT_API_KEY=your-farmanout-api-key
SERVER_RESPONSE_TIME=60.0
```

### Running Locally

```bash
cd src
python manage.py migrate
python manage.py runserver
```

### API Base URL

- Local: `http://localhost:8000/api/`
- Production: `https://your-app.vercel.app/api/`

## Authentication

The API uses JWT (JSON Web Token) authentication.

### Obtain Token

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

### Token Configuration

| Setting | Value |
|---------|-------|
| Access Token Lifetime | 60 minutes |
| Refresh Token Lifetime | 7 days |

### Using the Token

Include the access token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

## Core Concepts

### Farm/Field

A Farm represents a monitored agricultural field with:
- Geographic coordinates (polygon boundary)
- Crop type
- Sowing date
- Last satellite observation date

### Satellite Indices

The system tracks 11 vegetation/environmental indices:

| Index | Full Name | Purpose |
|-------|-----------|---------|
| NDVI | Normalized Difference Vegetation Index | Vegetation health |
| SAVI | Soil Adjusted Vegetation Index | Vegetation in sparse areas |
| EVI | Enhanced Vegetation Index | Dense vegetation monitoring |
| NDRE | Normalized Difference Red Edge | Chlorophyll content |
| RSM | Root Zone Soil Moisture | Soil moisture levels |
| NDWI | Normalized Difference Water Index | Water content |
| NDMI | Normalized Difference Moisture Index | Moisture stress |
| ET | Evapotranspiration | Water loss |
| SOC | Soil Organic Carbon | Soil health |
| ETCI | ETCI Index | Combined index |
| RVI | Ratio Vegetation Index | Vegetation ratio |

### Crop Loss Scenarios

The system monitors three types of crop loss scenarios:

| Scenario | Trigger Condition |
|----------|-------------------|
| Flood | Rain > 75mm in weather forecast |
| Drought | NDMI < 30 for 4 consecutive satellite visits |
| Pest | High probability pest detection in 4 consecutive advisories |

## Deployment

### Vercel

The project includes `vercel.json` for serverless deployment on Vercel.

### Railway

Use `railway.toml` for Railway deployment with Docker.

### Docker

```bash
docker build -t ak-backend .
docker run -p 8000:8000 ak-backend
```

## License

This project is proprietary software.
