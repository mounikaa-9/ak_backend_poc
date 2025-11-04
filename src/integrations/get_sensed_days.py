import os
import json
from datetime import datetime
from time import perf_counter
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def get_sensed_days(field_id : str):
    server_response_time = float(os.getenv('SERVER_RESPONSE_TIME'))
    endpoint_url = "https://us-central1-farmbase-b2f7e.cloudfunctions.net/getSensedDays"
    body_obj = {
        "FieldID": field_id,
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
                "api" : "get_sensed_days",
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
            "api" : "get_sensed_days",
            "error": "Connection timed out while contacting server"
        }

    except httpx.ReadTimeout:
        return {
            "api" : "get_sensed_days",
            "error": "Server took too long to respond"
        }

    except httpx.ConnectError:
        return {
            "api" : "get_sensed_days",
            "error": "Failed to connect to server. Check your internet or endpoint URL"
        }

    except httpx.HTTPStatusError as e:
        # Raised by response.raise_for_status()
        return {
            "api" : "get_sensed_days",
            "error": f"HTTP error occurred: {e.response.status_code}",
            "details": e.response.text
        }
        

# if __name__ == "__main__":
#     res = asyncio.run(get_sensed_days("1760077640806"))
#     print(res)