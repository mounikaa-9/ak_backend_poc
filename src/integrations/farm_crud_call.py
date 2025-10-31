import os
import json

from typing import List
from datetime import datetime
from time import perf_counter
import httpx
import asyncio
from dotenv import load_dotenv

def latlong_to_longlat(points: List):
    """
    Converts a list of [latitude, longitude] pairs 
    to [longitude, latitude] pairs for the api call
    """
    return [[lon, lat] for lat, lon in points]

async def add_new_farm(
    crop_name : str,
    full_name : str,
    date : datetime,
    points : List, # should be in the lat-long
    payment_type : int = 1,
):
        
    crop_code = {
        "rice" : 1,
        "turmeric" : 21,
        "soyabean" : 11,
        "chickpea" : 8,
        "red gram" : 9,
        "black gram" : 45,
        "green gram" : 64
    }
    load_dotenv()
    server_response_time = float(os.getenv('SERVER_RESPONSE_TIME'))
    endpoint_url = "https://us-central1-farmbase-b2f7e.cloudfunctions.net/submitField"

    def date_to_epoch(date_value : datetime):
        """
        Converts a YYYYMMDD date (string or int) to epoch timestamp (seconds).
        Ensures the date is not later than today (UTC).
        """
        # Convert to string and parse
        date_str = str(date_value)
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return int(dt.timestamp())
    
    body_obj = {
        "CropCode" : crop_code.get(crop_name),
        "FieldName" : full_name,
        "PaymentType" : payment_type,
        "SowingDate" : date_to_epoch(date_value = date),
        "Points" : latlong_to_longlat(points)
    }

    headers_obj = {
        "Authorization": f"Bearer {os.getenv('FARMANOUT_API_KEY')}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=server_response_time) as client:
            response = await client.post(endpoint_url, headers=headers_obj, json=body_obj)
            response.raise_for_status()  # Raise exception for 4xx/5xx

        try:
            res = response.json()
            return {
                "api" : "add_new_farm",
                "field_id" : res["FieldID"],
                "field_area" : res["hUnits"]
            }
        except json.JSONDecodeError:
            return {
                "error": "Invalid JSON response from server",
                "status_code": response.status_code,
                "response_text": response.text
            }

    except httpx.ConnectTimeout:
        return {
            "api" : "add_new_farm",
            "error": "Connection timed out while contacting server"
        }

    except httpx.ReadTimeout:
        return {
            "api" : "add_new_farm",
            "error": "Server took too long to respond"
        }

    except httpx.ConnectError:
        return {
            "api" : "add_new_farm",
            "error": "Failed to connect to server. Check your internet or endpoint URL"
        }

    except httpx.HTTPStatusError as e:
        # Raised by response.raise_for_status()
        return {
            "api" : "add_new_farm",
            "error": f"HTTP error occurred: {e.response.status_code}",
            "details": e.response.text
        }
        
async def edit_field_boundary(field_id : str, points : List):
    load_dotenv()
    server_response_time = os.getenv('SERVER_RESPONSE_TIME')
    endpoint_url = "https://us-central1-farmbase-b2f7e.cloudfunctions.net/modifyFieldPoints"

    body_obj = {
        "Points" : latlong_to_longlat(points = points),
        "FieldID": str(field_id),
    }

    headers_obj = {
        "Authorization": f"Bearer {os.getenv('FARMANOUT_API_KEY')}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=server_response_time) as client:
            response = await client.post(endpoint_url, headers=headers_obj, json=body_obj)
            response.raise_for_status()  # Raise exception for 4xx/5xx

        try:
            last_date_obj = max(
                (datetime.strptime(str(k), "%Y%m%d") for k in dict(response.json()).keys())
            )
            last_date = last_date_obj.strftime("%Y%m%d")
            return {
                "api" : "edit_field_boundary",
                "last_sensed_day" : last_date
            }
        except json.JSONDecodeError:
            return {
                "error": "Invalid JSON response from server",
                "status_code": response.status_code,
                "response_text": response.text
            }

    except httpx.ConnectTimeout:
        return {
            "api" : "edit_field_boundary",
            "error": "Connection timed out while contacting server"
        }

    except httpx.ReadTimeout:
        return {
            "api" : "edit_field_boundary",
            "error": "Server took too long to respond"
        }

    except httpx.ConnectError:
        return {
            "api" : "edit_field_boundary",
            "error": "Failed to connect to server. Check your internet or endpoint URL"
        }

    except httpx.HTTPStatusError as e:
        # Raised by response.raise_for_status()
        return {
            "api" : "edit_field_boundary",
            "error": f"HTTP error occurred: {e.response.status_code}",
            "details": e.response.text
        }
        
# if __name__ == "__main__":
#     res = asyncio.run(add_new_farm(
#         crop_name = "rice",
#         full_name = "testing_field_1_suser",
#         date = "2025-10-01",
#         points = [
#         [15.678440, 77.756490],
#         [15.678199, 77.757107],
#         [15.679233, 77.757575],
#         [15.679458, 77.757124],
#         [15.679185, 77.756507]]
#     ))
#     with open('results_add.json', 'w') as f:
#         json.dump(res, f, indent = 4)