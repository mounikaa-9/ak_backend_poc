import os
import json
import logging
from typing import List, Dict, Any
import time
from datetime import datetime, timedelta
import asyncio

from ninja import Router
from ninja.errors import HttpError
from ninja.security import django_auth
from ninja_jwt.authentication import JWTAuth

from dotenv import load_dotenv

import traceback

from utils.az_upload import upload_field_images_to_azure
from integrations.get_sensed_days import get_sensed_days
from integrations.ai_advisory_crud_call import get_ai_advisory
from integrations.weather_crud_call import weather_forecast
from integrations.heatmaps_crud import get_all_images
from integrations.index_values_crud_call import get_index_values
from users.models import Farm
from users.farm_schemas import FarmResponseSchema
from heatmaps.utils import save_heatmaps_from_response, save_index_values_from_response
from ai_advisory.utils import save_ai_adviosry_from_response
from weather.utils import save_weather_from_response
from crop_loss_analytics.models import CropLossAnalytics
from pipelines.new_profile_script import creation_router

load_dotenv()

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

def process_heatmaps(field_id: str, sensed_day: str) -> Dict[str, Any]:
    """Process and save heatmaps"""
    result = {"success": False, "error": None}
    try:
        url_files = asyncio.run(get_all_images(field_id=field_id, sensed_day=sensed_day))
        results = upload_field_images_to_azure(field_data=url_files)
        save_heatmaps_from_response(field_data=results)
        logger.info(f"Heatmaps uploaded and saved for {field_id}")
        result["success"] = True
    except Exception as e:
        error_msg = f"Image upload or heatmap save failed for {field_id}: {e}"
        logger.error(error_msg)
        traceback.print_exc()
        result["error"] = str(e)
    return result


def process_index_values(field_id: str, sensed_day: str) -> Dict[str, Any]:
    """Fetch and save index values"""
    result = {"success": False, "error": None, "data": {}}
    try:
        index_values = asyncio.run(get_index_values(field_id=field_id, sensed_day=sensed_day))
        save_index_values_from_response(field_data=index_values)
        logger.info(f"Index values saved for {field_id}: {index_values}")
        result["success"] = True
        result["data"] = index_values
    except Exception as e:
        error_msg = f"Index value retrieval failed for {field_id}: {e}"
        logger.error(error_msg)
        traceback.print_exc()
        result["error"] = str(e)
    return result


def process_ai_advisory(field_id: str, crop: str) -> Dict[str, Any]:
    """Fetch and save AI advisory"""
    result = {"success": False, "error": None, "data": {}}
    try:
        ai_response = asyncio.run(get_ai_advisory(field_id=field_id, crop=crop))
        save_ai_adviosry_from_response(api_response=ai_response, field_id=field_id)
        logger.info(f"AI advisory saved for {field_id}")
        result["success"] = True
        result["data"] = ai_response
    except Exception as e:
        error_msg = f"AI advisory failed for {field_id}: {e}"
        logger.error(error_msg)
        traceback.print_exc()
        result["error"] = str(e)
    return result


def process_weather(field_id: str) -> Dict[str, Any]:
    """Fetch and save weather forecast"""
    result = {"success": False, "error": None, "data": {}}
    try:
        weather_response = asyncio.run(weather_forecast(field_id=field_id))
        weather_response = weather_response.get("weather", {})
        save_weather_from_response(weather_response)
        logger.info(f"Weather data saved for {field_id}")
        result["success"] = True
        result["data"] = weather_response
    except Exception as e:
        error_msg = f"Weather data failed for {field_id}: {e}"
        logger.error(error_msg)
        traceback.print_exc()
        result["error"] = str(e)
    return result


def has_high_probability_pest(data: dict) -> bool:
    """Check if AI response has high probability pest detection"""
    try:
        pests = data.get("Pest and Disease", {}).get("potential_pests", [])
        for pest in pests:
            if pest.get("probability", "").lower() == "high":
                return True
    except Exception:
        pass
    return False


def create_flood_analytics(farm: Farm, weather_response: dict, field_id: str, last_day_sensed: datetime) -> Dict[str, Any]:
    """Create or update flood analytics if conditions are met"""
    result = {"success": False, "error": None, "action": "none"}
    try:
        if (
            weather_response
            and "daily" in weather_response
            and len(weather_response["daily"]) > 0
            and float(weather_response["daily"][0].get("rain", -1)) > 75
        ):
            time_delta = timedelta(days=3)
            date_end = datetime.now() + time_delta
            
            # Try to get existing active analytics
            existing = CropLossAnalytics.objects.filter(
                farm=farm,
                kind="flood",
                is_active=True
            ).first()
            
            if existing:
                # Update if new last_day_sensed is closer to date_end
                existing_distance = abs((existing.date_end - existing.closest_date_sensed).total_seconds())
                new_distance = abs((date_end - last_day_sensed).total_seconds())
                
                if new_distance < existing_distance:
                    existing.closest_date_sensed = last_day_sensed
                
                existing.date_current = datetime.now()
                existing.date_end = date_end
                existing.save()
                logger.info(f"Flood analytics updated for {field_id}")
                result["action"] = "updated"
            else:
                # Create new analytics
                CropLossAnalytics.objects.create(
                    farm=farm,
                    kind="flood",
                    date_start=last_day_sensed,
                    date_current=datetime.now(),
                    date_end=date_end,
                    closest_date_sensed=last_day_sensed
                )
                logger.info(f"Flood analytics created for {field_id}")
                result["action"] = "created"
            
            result["success"] = True
    except Exception as e:
        error_msg = f"Flood loss analytics failed for {field_id}: {e}"
        logger.error(error_msg)
        traceback.print_exc()
        result["error"] = str(e)
    return result


def create_drought_analytics(farm: Farm, index_values: dict, field_id: str, last_day_sensed: datetime) -> Dict[str, Any]:
    """Create or update drought analytics if conditions are met"""
    result = {"success": False, "error": None, "action": "none"}
    try:
        if float(index_values.get("ndmi", -1)) != -1 and float(index_values["ndmi"]) < 30:
            time_delta = timedelta(days=30)
            date_end = datetime.now() + time_delta
            
            # Try to get existing active analytics
            existing = CropLossAnalytics.objects.filter(
                farm=farm,
                kind="drought",
                is_active=True
            ).first()
            
            if existing:
                # Update if new last_day_sensed is closer to date_end
                existing_distance = abs((existing.date_end - existing.closest_date_sensed).total_seconds())
                new_distance = abs((date_end - last_day_sensed).total_seconds())
                
                if new_distance < existing_distance:
                    existing.closest_date_sensed = last_day_sensed
                
                existing.date_current = datetime.now()
                existing.date_end = date_end
                existing.save()
                logger.info(f"Drought analytics updated for {field_id}")
                result["action"] = "updated"
            else:
                # Create new analytics
                CropLossAnalytics.objects.create(
                    farm=farm,
                    kind="drought",
                    date_start=last_day_sensed,
                    date_current=datetime.now(),
                    date_end=date_end,
                    closest_date_sensed=last_day_sensed
                )
                logger.info(f"Drought analytics created for {field_id}")
                result["action"] = "created"
            
            result["success"] = True
    except Exception as e:
        error_msg = f"Drought loss analytics failed for {field_id}: {e}"
        logger.error(error_msg)
        traceback.print_exc()
        result["error"] = str(e)
    return result


def create_pest_analytics(farm: Farm, ai_response: dict, field_id: str, last_day_sensed: datetime) -> Dict[str, Any]:
    """Create or update pest analytics if conditions are met"""
    result = {"success": False, "error": None, "action": "none"}
    try:
        if has_high_probability_pest(ai_response.get("advisory", {})):
            time_delta = timedelta(days=3)
            date_end = datetime.now() + time_delta
            
            # Try to get existing active analytics
            existing = CropLossAnalytics.objects.filter(
                farm=farm,
                kind="pest",
                is_active=True
            ).first()
            
            if existing:
                # Update if new last_day_sensed is closer to date_end
                existing_distance = abs((existing.date_end - existing.closest_date_sensed).total_seconds())
                new_distance = abs((date_end - last_day_sensed).total_seconds())
                
                if new_distance < existing_distance:
                    existing.closest_date_sensed = last_day_sensed
                
                existing.date_current = datetime.now()
                existing.date_end = date_end
                existing.save()
                logger.info(f"Pest analytics updated for {field_id}")
                result["action"] = "updated"
            else:
                # Create new analytics
                CropLossAnalytics.objects.create(
                    farm=farm,
                    kind="pest",
                    date_start=last_day_sensed,
                    date_current=datetime.now(),
                    date_end=date_end,
                    closest_date_sensed=last_day_sensed
                )
                logger.info(f"Pest analytics created for {field_id}")
                result["action"] = "created"
            
            result["success"] = True
    except Exception as e:
        error_msg = f"Pest loss analytics failed for {field_id}: {e}"
        logger.error(error_msg)
        traceback.print_exc()
        result["error"] = str(e)
    return result


def update_all_data(farm: Farm, field_id: str, crop: str, new_sensed_day: str) -> Dict[str, Any]:
    """Update all farm data when there's a new sensed day"""
    logger.info(f"New sensed day detected for {field_id}: {new_sensed_day}")
    
    # Parse the sensed day to datetime - handle format YYYYMMDD
    try:
        # The format from logs shows: 20251029 (YYYYMMDD without separators)
        last_day_sensed_dt = datetime.strptime(new_sensed_day, "%Y%m%d")
    except ValueError:
        try:
            # Fallback to YYYY-MM-DD format
            last_day_sensed_dt = datetime.strptime(new_sensed_day, "%Y-%m-%d")
        except ValueError:
            logger.warning(f"Could not parse sensed day {new_sensed_day}, using current datetime")
            last_day_sensed_dt = datetime.now()
    
    # Process all tasks and collect results
    results = {
        "heatmaps": process_heatmaps(field_id, new_sensed_day),
        "index_values": process_index_values(field_id, new_sensed_day),
        "ai_advisory": process_ai_advisory(field_id, crop),
        "weather": process_weather(field_id),
    }
    
    # Extract data for analytics
    index_values = results["index_values"]["data"] if results["index_values"]["success"] else {}
    ai_response = results["ai_advisory"]["data"] if results["ai_advisory"]["success"] else {}
    weather_response = results["weather"]["data"] if results["weather"]["success"] else {}
    
    # Create analytics based on the results
    results["flood_analytics"] = create_flood_analytics(farm, weather_response, field_id, last_day_sensed_dt)
    results["drought_analytics"] = create_drought_analytics(farm, index_values, field_id, last_day_sensed_dt)
    results["pest_analytics"] = create_pest_analytics(farm, ai_response, field_id, last_day_sensed_dt)
    
    return results


def update_weather_only(field_id: str) -> Dict[str, Any]:
    """Update only weather data when sensed day hasn't changed"""
    logger.info(f"No new sensed day for {field_id}, updating weather only")
    return {"weather": process_weather(field_id)}


@creation_router.post("/sync_create_entire_profile", auth=JWTAuth())
def reload_logic(request, payload: FarmResponseSchema):
    """Synchronous reload logic"""
    user = request.user
    field_id = str(payload.field_id)
    crop = payload.crop
    logger.info(f"Starting profile creation for field_id={field_id}, user={user.username}, crop={crop}")

    # Get the farm object
    try:
        farm = Farm.objects.get(user=request.user, field_id=field_id)
        logger.info(f"Farm found for user={user.username}, field_id={field_id}")
    except Farm.DoesNotExist:
        logger.error(f"Farm not found for user={user.username}, field_id={field_id}")
        raise HttpError(404, "Farm Not Found")

    # Get current and new sensed days
    current_sensed_day = farm.last_sensed_day
    try:
        response_ = asyncio.run(get_sensed_days(field_id=field_id))
        new_sensed_day = response_["last_sensed_day"]
        if new_sensed_day is None:
            raise ValueError("No sensed day found yet")
        logger.info(f"Sensed day fetched successfully for {field_id}: {new_sensed_day}")
    except Exception as e:
        logger.warning(f"get_sensed_days failed for {field_id}: {e}")
        traceback.print_exc()
        raise HttpError(408, "Currently Loading Screens")

    # Determine if we need full update or just weather update
    has_new_sensed_day = (current_sensed_day is None or 
                          str(current_sensed_day) != str(new_sensed_day))
    
    if has_new_sensed_day:
        # Update farm with new sensed day
        try:
            farm.last_sensed_day = new_sensed_day
            farm.save()
            logger.info(f"Farm updated with last_sensed_day={new_sensed_day} for {field_id}")
        except Exception as e:
            logger.error(f"Failed to update farm {field_id}: {e}")
            traceback.print_exc()
            raise HttpError(500, "Failed to update farm")
        
        # Full update with all data
        try:
            update_results = update_all_data(farm, field_id, crop, new_sensed_day)
        except Exception as e:
            logger.error(f"Full update failed for {field_id}: {e}")
            traceback.print_exc()
            raise HttpError(500, f"Profile update failed: {str(e)}")
        
        # Count successes and failures
        success_count = sum(1 for r in update_results.values() if r.get("success", False))
        total_count = len(update_results)
        
        logger.info(f"Full profile update completed for {field_id}: {success_count}/{total_count} successful")
        return {
            "status": "success",
            "field_id": field_id,
            "last_sensed_day": str(new_sensed_day),
            "update_type": "full",
            "results": update_results,
            "summary": {
                "successful": success_count,
                "total": total_count
            }
        }
    else:
        # Only update weather
        try:
            update_results = update_weather_only(field_id)
        except Exception as e:
            logger.error(f"Weather update failed for {field_id}: {e}")
            traceback.print_exc()
            raise HttpError(500, f"Weather update failed: {str(e)}")
        
        logger.info(f"Weather-only update completed for {field_id}")
        return {
            "status": "success",
            "field_id": field_id,
            "last_sensed_day": str(current_sensed_day),
            "update_type": "weather_only",
            "results": update_results,
            "summary": {
                "successful": 1 if update_results["weather"]["success"] else 0,
                "total": 1
            }
        }