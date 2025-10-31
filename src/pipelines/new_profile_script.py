import os
import json
import logging
from typing import List
import time
from datetime import datetime, timedelta

from ninja import Router
from ninja.errors import HttpError
from ninja.security import django_auth
from ninja_jwt.authentication import JWTAuth

import asyncio
import traceback

from utils.az_upload import upload_field_images_to_azure
from integrations.get_sensed_days import get_sensed_days
from integrations.ai_advisory_crud_call import get_ai_advisory
from integrations.weather_crud_call import weather_forecast
from integrations.heatmaps_crud import get_all_images
from integrations.index_values_crud_call import get_index_values
from users.models import User, Farm
from users.farm_schemas import FarmResponseSchema
from heatmaps.models import Heatmap, IndexTimeSeries
from heatmaps.utils import save_heatmaps_from_response, save_index_values_from_response
from ai_advisory.models import Advisory
from ai_advisory.utils import save_ai_adviosry_from_response
from weather.models import WeatherPrediction
from weather.utils import save_weather_from_response
from crop_loss_analytics.models import CropLossAnalytics

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)

creation_router = Router(tags=["reload_router"])

@creation_router.post("/create_entire_profile", auth=JWTAuth())
def reload_logic(request, payload: FarmResponseSchema):
    user = request.user
    field_id = str(payload.field_id)
    crop = payload.crop
    logger.info(f"Starting profile creation for field_id={field_id}, user={user.username}, crop={crop}")

    # Get the farm object first
    try:
        farm = Farm.objects.get(user=request.user, field_id=field_id)
        logger.info(f"Farm found for user={user.username}, field_id={field_id}")
    except Farm.DoesNotExist:
        logger.error(f"Farm not found for user={user.username}, field_id={field_id}")
        raise HttpError(404, "Farm Not Found")

    # Get sensed days
    try:
        response_ = asyncio.run(get_sensed_days(field_id=field_id))
        last_sensed_day = response_["last_sensed_day"]
        if last_sensed_day is None:
            raise ValueError("No sensed day found yet")
        logger.info(f"Sensed day fetched successfully for {field_id}: {last_sensed_day}")
    except Exception as e:
        logger.warning(f"get_sensed_days failed for {field_id}: {e}")
        traceback.print_exc()
        raise HttpError(408, "Currently Loading Screens")

    # Update farm
    try:
        farm.last_sensed_day = last_sensed_day
        farm.save()
        logger.info(f"Farm updated with last_sensed_day={last_sensed_day} for {field_id}")
    except Exception as e:
        logger.error(f"Failed to update farm {field_id}: {e}")
        traceback.print_exc()
        raise HttpError(500, "Failed to update farm")

    # Image processing
    try:
        url_files = asyncio.run(get_all_images(field_id=field_id, sensed_day=last_sensed_day))
        results = upload_field_images_to_azure(field_data=url_files)
        save_heatmaps_from_response(field_data=results)
        logger.info(f"Heatmaps uploaded and saved for {field_id}")
    except Exception as e:
        logger.error(f"Image upload or heatmap save failed for {field_id}: {e}")
        traceback.print_exc()

    # Index values
    try:
        index_values = asyncio.run(get_index_values(field_id=field_id, sensed_day=last_sensed_day))
        save_index_values_from_response(field_data=index_values)
        logger.info(f"Index values saved for {field_id}: {index_values}")
    except Exception as e:
        logger.error(f"Index value retrieval failed for {field_id}: {e}")
        traceback.print_exc()
        index_values = {}

    # AI advisory
    try:
        ai_response = asyncio.run(get_ai_advisory(field_id=field_id, crop=crop))
        save_ai_adviosry_from_response(api_response=ai_response, field_id=field_id)
        logger.info(f"AI advisory saved for {field_id}")
    except Exception as e:
        logger.error(f"AI advisory failed for {field_id}: {e}")
        traceback.print_exc()
        ai_response = {}

    # Weather forecast
    try:
        weather_response = asyncio.run(weather_forecast(field_id=field_id))
        weather_response = weather_response.get("weather", {})
        save_weather_from_response(weather_response)
        logger.info(f"Weather data saved for {field_id}")
    except Exception as e:
        logger.error(f"Weather data failed for {field_id}: {e}")
        traceback.print_exc()
        weather_response = {}

    # Flood analytics
    try:
        if (
            weather_response
            and "daily" in weather_response
            and len(weather_response["daily"]) > 0
            and float(weather_response["daily"][0].get("rain", -1)) > 75
        ):
            time_delta = timedelta(days=3)
            CropLossAnalytics.objects.create(
                farm=farm,
                kind="flood",
                date_start=datetime.now(),
                date_current=datetime.now(),
                date_end=datetime.now() + time_delta
            )
            logger.info(f"Flood analytics created for {field_id}")
    except Exception as e:
        logger.error(f"Flood loss analytics failed for {field_id}: {e}")
        traceback.print_exc()

    # Drought analytics
    try:
        if float(index_values.get("ndmi", -1)) != -1 and float(index_values["ndmi"]) < 30:
            time_delta = timedelta(days=30)
            CropLossAnalytics.objects.create(
                farm=farm,
                kind="drought",
                date_start=datetime.now(),
                date_current=datetime.now(),
                date_end=datetime.now() + time_delta
            )
            logger.info(f"Drought analytics created for {field_id}")
    except Exception as e:
        logger.error(f"Drought loss analytics failed for {field_id}: {e}")
        traceback.print_exc()

    # Helper function for pest detection
    def has_high_probability_pest(data: dict) -> bool:
        try:
            pests = data.get("Pest and Disease", {}).get("potential_pests", [])
            for pest in pests:
                if pest.get("probability", "").lower() == "high":
                    return True
        except Exception:
            pass
        return False

    # Pest analytics
    try:
        if has_high_probability_pest(ai_response.get("advisory", {})):
            time_delta = timedelta(days=3)
            CropLossAnalytics.objects.create(
                farm=farm,
                kind="pest",
                date_start=datetime.now(),
                date_current=datetime.now(),
                date_end=datetime.now() + time_delta
            )
            logger.info(f"Pest analytics created for {field_id}")
    except Exception as e:
        logger.error(f"Pest loss analytics failed for {field_id}: {e}")
        traceback.print_exc()

    logger.info(f"Profile creation completed successfully for {field_id}")
    return {"status": "success", "field_id": field_id, "last_sensed_day": str(last_sensed_day)}