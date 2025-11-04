import os
import json
import asyncio
import httpx
from time import perf_counter
from dotenv import load_dotenv

async def get_ai_advisory(field_id: str, crop: str):
    load_dotenv()
    server_response_time = float(os.getenv('SERVER_RESPONSE_TIME', 60.0))
    endpoint_url = "https://us-central1-farmbase-b2f7e.cloudfunctions.net/askJeevnAPI"

    body_obj = {
        "Crop": crop,
        "FieldID": str(field_id)
    }

    headers_obj = {
        "Authorization": f"Bearer {os.getenv('FARMANOUT_API_KEY')}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=3*server_response_time) as client:
            response = await client.post(endpoint_url, headers=headers_obj, json=body_obj)
            response.raise_for_status()  # Raise exception for 4xx/5xx
        try:
            return response.json()
        except json.JSONDecodeError:
            return {
                "error": "Invalid JSON response from server",
                "status_code": response.status_code,
                "response_text": response.text
            }

    except httpx.ConnectTimeout:
        return {"error": "Connection timed out while contacting server"}

    except httpx.ReadTimeout:
        return {"error": "Server took too long to respond"}

    except httpx.ConnectError:
        return {"error": "Failed to connect to server. Check your internet or endpoint URL"}

    except httpx.HTTPStatusError as e:
        # Raised by response.raise_for_status()
        return {
            "error": f"HTTP error occurred: {e.response.status_code}",
            "details": e.response.text
        }

    except Exception as e:
        # Catch-all for any other unexpected errors
        return {"error": f"Unexpected error: {str(e)}"}


# if __name__ == "__main__":
#     start_time = perf_counter()
#     response = asyncio.run(get_ai_advisory(field_id="1762238407649", crop = "red gram"))
#     end_time = perf_counter()
#     print(end_time - start_time)
#     with open('ai_advisory_test.json', 'w') as f:
#         json.dump(response, f, indent=4)