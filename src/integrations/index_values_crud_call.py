import os
import json
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def get_index_values(
    field_id : str, 
    sensed_day: str
):
    required_fields = [
        'rvi',
        'ndvi',
        'savi',
        'evi',
        'ndre',
        'rsm',
        'ndwi',
        'ndmi',
        'et',
        'soc',
        'etci'
    ]
    endpoint_url = 'https://us-central1-farmbase-b2f7e.cloudfunctions.net/getAllIndexValues'
    body_obj = {
        "FieldID" : str(field_id)
    }
    
    server_response_time = float(os.getenv('SERVER_RESPONSE_TIME'))
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
                "api" : "get_index_values",
                "rvi" : res.get('rvi', {}).get(sensed_day, -1),
                "ndvi" : res.get('ndvi', {}).get(sensed_day, -1),
                "savi" : res.get('savi', {}).get(sensed_day, -1),
                "evi" : res.get('evi', {}).get(sensed_day, -1),
                "ndre" : res.get('ndre', {}).get(sensed_day, -1),
                "rsm" : res.get('rsm', {}).get(sensed_day, -1),
                "ndwi" : res.get('ndwi', {}).get(sensed_day, -1),
                "ndmi" : res.get('ndmi', {}).get(sensed_day, -1),
                "evapo" : res.get('evapo', {}).get(sensed_day, -1),
                "soc" : res.get('soc', {}).get(sensed_day, -1),
                "etci" : res.get('etci', {}).get(sensed_day, -1),
                "_meta" : {
                    "field_id" : field_id,
                    "sensed_day" : sensed_day
                }
            }
        except json.JSONDecodeError:
            return {
                "error": "Invalid JSON response from server",
                "status_code": response.status_code,
                "response_text": response.text,
                "_meta" : {
                    "field_id" : field_id,
                    "sensed_day" : sensed_day
                }
            }

    except httpx.ConnectTimeout:
        return {
            "api" : "get_index_values",
            "error": "Connection timed out while contacting server",
            "_meta" : {
                    "field_id" : field_id,
                    "sensed_day" : sensed_day
                }
        }

    except httpx.ReadTimeout:
        return {
            "api" : "get_index_values",
            "error": "Server took too long to respond",
            "_meta" : {
                    "field_id" : field_id,
                    "sensed_day" : sensed_day
                }
        }

    except httpx.ConnectError:
        return {
            "api" : "get_index_values",
            "error": "Failed to connect to server. Check your internet or endpoint URL",
            "_meta" : {
                    "field_id" : field_id,
                    "sensed_day" : sensed_day
                }
        }

    except httpx.HTTPStatusError as e:
        # Raised by response.raise_for_status()
        return {
            "api" : "get_index_values",
            "error": f"HTTP error occurred: {e.response.status_code}",
            "details": e.response.text,
            "_meta" : {
                    "field_id" : field_id,
                    "sensed_day" : sensed_day
                }
        }
        
# if __name__ == "__main__":
#     res = asyncio.run(
#         get_index_values(
#             field_id = "1761808284616",
#             sensed_day = "20251029"
#         )
#     )
#     with open('index_values.json', 'w') as f:
#         json.dump(res, f, indent = 4)
#     from pprint import pprint
#     pprint(res)