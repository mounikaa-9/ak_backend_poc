import os
from typing import Literal
from datetime import date
from django.db import DatabaseError
from ninja import Router
from ninja.errors import HttpError
from ninja_jwt.authentication import JWTAuth

import asyncio

from users.models import Farm
from crop_loss_analytics.models import CropLossAnalytics
from crop_loss_analytics.crop_loss_analytics_schema import CropLossAnalyticsResponseSchema

crop_loss_analytics_router = Router(tags = ["Crop Loss Analytics"])

@crop_loss_analytics_router.get(
    "/crop_loss_analytics",
    response = CropLossAnalyticsResponseSchema
)
def get_crop_loss_analytics(request, kind : Literal["flood", "pest", "drought"]):
    
    try:
        farm = Farm.objects.get(user=request.user)
    except Farm.DoesNotExist:
        raise HttpError(400, "Farm not found")
    
    qs = CropLossAnalytics.objects.filter(
        farm = farm,
        kind = kind,
        is_active = True
    ).first()
    
    if qs:
        return {
            "start_date" : date(qs.date_start),
            "approx_end_date" : date(qs.date_end),
            "kind" : kind
        }
    
    return {
        "kind" : kind,
        "start_date" : None,
        "end_date" : None
    }
    