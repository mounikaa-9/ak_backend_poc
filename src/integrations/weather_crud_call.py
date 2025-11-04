import os
import json

from typing import List
from datetime import datetime
from time import perf_counter
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def weather_forecast(
    field_id : str,
):
    server_response_time = float(os.getenv('SERVER_RESPONSE_TIME'))
    endpoint_url = "https://us-central1-farmbase-b2f7e.cloudfunctions.net/getPresentWeather"
    
    body_obj = {
        "FieldID" : field_id
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
                "api" : "weather_forecast",
                "weather" : res
            }
        except json.JSONDecodeError:
            return {
                "error": "Invalid JSON response from server",
                "status_code": response.status_code,
                "response_text": response.text
            }

    except httpx.ConnectTimeout:
        return {
            "api" : "weather_forecast",
            "error": "Connection timed out while contacting server"
        }

    except httpx.ReadTimeout:
        return {
            "api" : "weather_forecast",
            "error": "Server took too long to respond"
        }

    except httpx.ConnectError:
        return {
            "api" : "weather_forecast",
            "error": "Failed to connect to server. Check your internet or endpoint URL"
        }

    except httpx.HTTPStatusError as e:
        # Raised by response.raise_for_status()
        return {
            "api" : "weather_forecast",
            "error": f"HTTP error occurred: {e.response.status_code}",
            "details": e.response.text
        }