import os
import json
from datetime import datetime
from time import perf_counter
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def get_field_image(
    field_id : str, 
    sensed_day: str, 
    image_type: str
):
    server_response_time = float(os.getenv('SERVER_RESPONSE_TIME'))
    endpoint_url = "https://us-central1-farmbase-b2f7e.cloudfunctions.net/getFieldImage"

    body_obj = {
        "FieldID": str(field_id),
        "ImageType" : image_type,
        "SensedDay" : sensed_day
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
            return {
                "api" : "get_field_image",
                "image_type" : image_type,
                "url" : response.json()["url"]
            }
        except json.JSONDecodeError:
            return {
                "error": "Invalid JSON response from server",
                "status_code": response.status_code,
                "response_text": response.text
            }

    except httpx.ConnectTimeout:
        return {
            "api" : "get_field_image",
            "image_type" : image_type,
            "url" : None,
            "error": "Connection timed out while contacting server"
        }

    except httpx.ReadTimeout:
        return {
            "api" : "get_field_image",
            "image_type" : image_type,
            "url" : None,
            "error": "Server took too long to respond"
        }

    except httpx.ConnectError:
        return {
            "api" : "get_field_image",
            "image_type" : image_type,
            "url" : None,
            "error": "Failed to connect to server. Check your internet or endpoint URL"
        }

    except httpx.HTTPStatusError as e:
        # Raised by response.raise_for_status()
        return {
            "api" : "get_field_image",
            "image_type" : image_type,
            "url" : None,
            "error": f"HTTP error occurred: {e.response.status_code}",
            "details": e.response.text
        }

async def get_all_images(
    field_id : str,
    sensed_day : str
):

    image_types = {
        "NDVI": "ndvi",
        "NDWI": "ndwi",
        "EVAPO": "evapo",
        "NDMI": "ndmi",
        "EVI": "evi",
        "RVI": "rvi",
        "RSM": "rsm",
        "NDRE": "ndre",
        "VARI": "vari",
        "SAVI": "savi",
        "AVI": "avi",
        "BSI": "bsi",
        "SI": "si",
        "SOC": "soc",
        "TCI": "tci",
        "ETCI": "etci",
        "HYBRID": "hybrid",
        "COLORBLIND": "hybrid_blind",
        "DEM": "dem",
        "LULC": "lulc",
    }

    # concurrent call for all the types
    tasks = [
        get_field_image(field_id=field_id, sensed_day=sensed_day, image_type=code)
        for code in image_types.values()
    ]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    result = {}
    for resp in responses:
        if isinstance(resp, Exception):
            continue
        img_type = resp.get("image_type")
        url = resp.get("url")
        result[img_type] = url if url else None

    result["_meta"] = {
        "field_id": field_id,
        "sensed_day": sensed_day,
        "timestamp": datetime.now().isoformat()
    }

    # output_filename = f"field_{field_id}_{sensed_day}.json"
    # with open(output_filename, "w") as f:
    #     json.dump(result, f, indent=4)
        
    return result

# if __name__ == "__main__":
#     start_time = perf_counter()
#     asyncio.run(
#         get_all_images(
#             field_id="1761808284616",
#             sensed_day="20251029"
#         )
#     )
#     end_time = perf_counter()
#     print(end_time - start_time)