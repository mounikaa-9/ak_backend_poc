import os
import logging

from ninja import Router
from ninja.errors import HttpError
from ninja.security import django_auth
from ninja_jwt.authentication import JWTAuth

from dotenv import load_dotenv

import traceback
from asgiref.sync import sync_to_async
from integrations.get_sensed_days import get_sensed_days
from integrations.ai_advisory_crud_call import get_ai_advisory
from users.models import Farm
from users.farm_schemas import FarmResponseSchema
from heatmaps.models import Heatmap, IndexTimeSeries
from ai_advisory.models import Advisory
from ai_advisory.utils import save_ai_adviosry_from_response
from weather.models import WeatherPrediction
from pipelines.new_profile_script import (
    process_ai_advisory, 
    process_heatmaps, 
    process_index_values, 
    process_weather
)

load_dotenv()
testing_router = Router(tags = ["testing_indi_functions"])

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

#endpoint to check each function individually
@testing_router.post("/debug_individual_calls", auth=JWTAuth())
async def debug_individual_calls(request, payload: FarmResponseSchema):
    """Test each API call individually to see which one fails"""
    field_id = str(payload.field_id)
    crop = payload.crop
    
    results = {}
    
    # Test 1: Get sensed days
    logger.info("=" * 80)
    logger.info("TEST 1: Getting sensed days")
    try:
        response_ = await get_sensed_days(field_id=field_id)
        new_sensed_day = response_["last_sensed_day"]
        results['sensed_days'] = {'success': True, 'data': new_sensed_day}
        logger.info(f"✅ Sensed days: {new_sensed_day}")
    except Exception as e:
        results['sensed_days'] = {'success': False, 'error': str(e)}
        logger.error(f"❌ Sensed days failed: {e}")
        traceback.print_exc()
    
    # Test 2: Heatmaps
    logger.info("=" * 80)
    logger.info("TEST 2: Processing heatmaps")
    try:
        sensed_day = results.get('sensed_days', {}).get('data', '20251103')
        await process_heatmaps(field_id, sensed_day)
        results['heatmaps'] = {'success': True}
        logger.info("✅ Heatmaps completed")
    except Exception as e:
        results['heatmaps'] = {'success': False, 'error': str(e)}
        logger.error(f"❌ Heatmaps failed: {e}")
        traceback.print_exc()
    
    # Test 3: Index values
    logger.info("=" * 80)
    logger.info("TEST 3: Processing index values")
    try:
        sensed_day = results.get('sensed_days', {}).get('data', '20251103')
        index_values = await process_index_values(field_id, sensed_day)
        results['index_values'] = {'success': True, 'data': index_values}
        logger.info(f"✅ Index values completed: {index_values}")
    except Exception as e:
        results['index_values'] = {'success': False, 'error': str(e)}
        logger.error(f"❌ Index values failed: {e}")
        traceback.print_exc()
    
    # Test 4: AI Advisory
    logger.info("=" * 80)
    logger.info("TEST 4: Processing AI advisory")
    try:
        ai_response = await process_ai_advisory(field_id, crop)
        results['ai_advisory'] = {'success': True, 'has_data': bool(ai_response)}
        logger.info(f"✅ AI advisory completed, has data: {bool(ai_response)}")
    except Exception as e:
        results['ai_advisory'] = {'success': False, 'error': str(e)}
        logger.error(f"❌ AI advisory failed: {e}")
        traceback.print_exc()
    
    # Test 5: Weather
    logger.info("=" * 80)
    logger.info("TEST 5: Processing weather")
    try:
        weather_response = await process_weather(field_id)
        results['weather'] = {'success': True, 'has_data': bool(weather_response)}
        logger.info(f"✅ Weather completed, has data: {bool(weather_response)}")
    except Exception as e:
        results['weather'] = {'success': False, 'error': str(e)}
        logger.error(f"❌ Weather failed: {e}")
        traceback.print_exc()
    
    # Test 6: Check database
    logger.info("=" * 80)
    logger.info("TEST 6: Checking database")
    try:
        farm = await sync_to_async(Farm.objects.get, thread_sensitive=False)(
            user=request.user, 
            field_id=field_id
        )
        
        # Check what was saved
        heatmap_count = await sync_to_async(Heatmap.objects.filter(farm=farm).count, thread_sensitive=False)()
        advisory_count = await sync_to_async(Advisory.objects.filter(farm=farm).count, thread_sensitive=False)()
        weather_count = await sync_to_async(WeatherPrediction.objects.filter(farm=farm).count, thread_sensitive=False)()
        index_count = await sync_to_async(IndexTimeSeries.objects.filter(farm=farm).count, thread_sensitive=False)()
        
        results['database'] = {
            'success': True,
            'heatmaps': heatmap_count,
            'advisories': advisory_count,
            'weather': weather_count,
            'index_values': index_count,
            'last_sensed_day': str(farm.last_sensed_day) if farm.last_sensed_day else None
        }
        logger.info(f"✅ Database check: heatmaps={heatmap_count}, advisories={advisory_count}, weather={weather_count}, index={index_count}")
    except Exception as e:
        results['database'] = {'success': False, 'error': str(e)}
        logger.error(f"❌ Database check failed: {e}")
        traceback.print_exc()
    
    logger.info("=" * 80)
    return results


# Also add this simpler test for the AI advisory specifically
@testing_router.post("/debug_ai_advisory_only", auth=JWTAuth())
async def debug_ai_advisory_only(request, payload: FarmResponseSchema):
    """Test ONLY the AI advisory call"""
    field_id = str(payload.field_id)
    crop = payload.crop
    
    logger.info("=" * 80)
    logger.info(f"TESTING AI ADVISORY - field_id={field_id}, crop={crop}")
    logger.info(f"API Key present: {bool(os.getenv('FARMANOUT_API_KEY'))}")
    logger.info(f"API Key length: {len(os.getenv('FARMANOUT_API_KEY', ''))}")
    
    try:
        # Call the raw function
        logger.info("Calling get_ai_advisory...")
        ai_response = await get_ai_advisory(field_id=field_id, crop=crop)
        
        logger.info(f"Response type: {type(ai_response)}")
        logger.info(f"Response keys: {list(ai_response.keys()) if isinstance(ai_response, dict) else 'Not a dict'}")
        
        if 'error' in ai_response:
            logger.error(f"Error in response: {ai_response['error']}")
            return {
                'success': False,
                'error': ai_response['error'],
                'full_response': ai_response
            }
        
        logger.info("Calling save function...")
        await sync_to_async(save_ai_adviosry_from_response, thread_sensitive=False)(
            api_response=ai_response,
            field_id=field_id
        )
        
        logger.info("Checking database...")
        farm = await sync_to_async(Farm.objects.get, thread_sensitive=False)(
            user=request.user,
            field_id=field_id
        )
        advisory_count = await sync_to_async(Advisory.objects.filter(farm=farm).count, thread_sensitive=False)()
        
        logger.info(f"✅ SUCCESS - Advisories in DB: {advisory_count}")
        return {
            'success': True,
            'advisory_count': advisory_count,
            'response_keys': list(ai_response.keys())
        }
        
    except Exception as e:
        logger.error(f"❌ EXCEPTION: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }