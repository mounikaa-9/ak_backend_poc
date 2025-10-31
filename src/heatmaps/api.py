from typing import List
from datetime import date, timedelta, datetime

from ninja import Router
from ninja.errors import HttpError
from ninja.security import django_auth
from ninja_jwt.authentication import JWTAuth
from django.contrib.auth.hashers import make_password

import asyncio

from users.models import Farm
from heatmaps.models import Heatmap, IndexTimeSeries
from heatmaps.heatmap_schemas import (
    HeatmapSchema, 
    HeatmapURLSchema
)
from heatmaps.time_series_schemas import (
    IndexTimeSeriesRequestSchema, 
    IndexTimeSeriesResponseSchema, 
    IndexValueDateSchema
)

heatmaps_router = Router(tags = ["heatmaps", "statellite-specific-time-series"])

@heatmaps_router.get(
    path="/get_heatmaps",
    auth=[JWTAuth(), django_auth],
    response=HeatmapSchema
)
def get_heatmap_url(request, farm_id: str, index_type: str, sensed_date: str):
    """Get heatmap URL from storage"""
    try:
        farm = Farm.objects.get(field_id=farm_id)
    except Farm.DoesNotExist:
        raise HttpError(400, "farm not found")

    try:
        date_obj = datetime.strptime(sensed_date, "%Y%m%d").date()
    except ValueError:
        raise HttpError(400, "Invalid date format. Expected YYYYMMDD.")

    heatmap = Heatmap.objects.filter(
        farm=farm,
        index_type=index_type,
        date=date_obj
    ).first()

    if not heatmap:
        raise HttpError(400, "heatmap not found")

    return {
        "farm_id": farm_id,
        "index_type": index_type,
        "date": date_obj,
        "image_url": heatmap.image_url
    }

@heatmaps_router.get(
    path="/get_past_satellite_values",
    response=IndexTimeSeriesResponseSchema
)
def get_past_satellite_data(request, farm_id : str, index_type : str):
    """Return satellite index values (with dates) for the last 30 days"""
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)
    try:
        farm = Farm.objects.get(field_id=farm_id)
    except Farm.DoesNotExist:
        raise HttpError(400, "farm not found")
    queryset = (
        IndexTimeSeries.objects
        .filter(
            farm=farm,
            index_type=index_type,
            date__gte=thirty_days_ago,
            date__lte=today
        )
        .order_by("date")
        .values("date", "value")
    )

    data = [IndexValueDateSchema(**entry) for entry in queryset]

    return {
        "farm_id": farm_id,
        "index_type": index_type,
        "data": data
    }