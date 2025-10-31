from typing import List
from datetime import datetime

from ninja import Router
from ninja.errors import HttpError
from ninja.security import django_auth
from ninja_jwt.authentication import JWTAuth

import asyncio

from users.models import Farm
from ai_advisory.models import Advisory

ai_advisory_router = Router(tags = ["ai_advisory"])

@ai_advisory_router.get(
    path="/get_ai_advisory",
    auth=JWTAuth()
)
def get_ai_advisory(request, field_id: str, sensed_date: str):
    try:
        farm = Farm.objects.get(field_id=field_id)
    except Farm.DoesNotExist:
        raise HttpError(400, "Farm not found")

    try:
        date_obj = datetime.strptime(sensed_date, "%Y%m%d").date()
    except ValueError:
        raise HttpError(400, "Invalid date format. Expected YYYYMMDD.")

    try:
        ai_advisory = Advisory.objects.get(farm=farm, sensed_day=date_obj)
    except Advisory.DoesNotExist:
        raise HttpError(404, "No advisory found for this field and date")

    return {
        "FIELD_METADATA": ai_advisory.get_field_metadata(),
        "FERTILIZER_ADVISORY": ai_advisory.get_fertilizer_advisory(),
        "IRRIGATION_ADVISORY": ai_advisory.get_irrigation_advisory(),
        "GROWTH_YIELD_ADVISORY": ai_advisory.get_growth_yield_advisory(),
        "WEED_ADVISORY": ai_advisory.get_weed_advisory(),
        "PEST_DISEASE_ADVISORY": ai_advisory.get_pest_disease_advisory(),
        "SOIL_MANAGEMENT_ADVISORY": ai_advisory.get_soil_management_advisory(),
    }