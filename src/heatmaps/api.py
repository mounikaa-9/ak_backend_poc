import os
from typing import List
from datetime import date, timedelta, datetime

from ninja import Router
from ninja.errors import HttpError
from ninja.security import django_auth
from ninja_jwt.authentication import JWTAuth
from django.contrib.auth.hashers import make_password

import asyncio
from dotenv import load_dotenv

from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions

from users.models import Farm
from heatmaps.models import Heatmap, IndexTimeSeries
from heatmaps.heatmap_schemas import (
    HeatmapSchema, 
    HeatmapURLSchema
)
from heatmaps.time_series_schemas import (
    IndexTimeSeriesResponseSchema, 
    IndexValueDateSchema,
    IndexValueDateResponseSchema
)

heatmaps_router = Router(tags = ["heatmaps", "statellite-specific-time-series"])

def generate_sas_url(blob_url: str, expiry_minutes: int = 60) -> str:
    """
    Generate a secure SAS URL for a given blob URL.
    
    Args:
        blob_url: The full blob URL (e.g., https://account.blob.core.windows.net/container/path/file.png)
        expiry_minutes: How long the SAS token should be valid (default: 60 minutes)
    
    Returns:
        Blob URL with SAS token appended
    """
    try:
        load_dotenv()
        connection_string = os.getenv("AZURE_CONNECTION_STRING")
        
        if not connection_string:
            raise Exception("AZURE_CONNECTION_STRING not configured")
        
        # Parse blob URL to extract components
        from urllib.parse import urlparse
        parsed = urlparse(blob_url)
        path_parts = parsed.path.lstrip('/').split('/', 1)
        
        if len(path_parts) < 2:
            raise ValueError(f"Invalid blob URL format: {blob_url}")
        
        container_name = path_parts[0]
        blob_name = path_parts[1]
        
        # Extract account name and key from connection string
        account_name = None
        account_key = None
        
        for part in connection_string.split(';'):
            if part.startswith('AccountName='):
                account_name = part.split('=', 1)[1]
            elif part.startswith('AccountKey='):
                account_key = part.split('=', 1)[1]
        
        if not account_name or not account_key:
            raise ValueError("Invalid connection string format")
        
        # Create blob service client to verify blob exists
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        
        # Verify blob exists
        if not blob_client.exists():
            raise FileNotFoundError(f"Blob not found: {blob_name}")
        
        # Generate SAS token
        sas_token = generate_blob_sas(
            account_name=account_name,
            account_key=account_key,
            container_name=container_name,
            blob_name=blob_name,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(minutes=expiry_minutes),
            start=datetime.utcnow() - timedelta(minutes=5)  # Account for clock skew
        )
        
        # Return URL with SAS token
        sas_url = f"{blob_url}?{sas_token}"
        return sas_url
        
    except Exception as e:
        # Log the error but don't expose internal details
        print(f"Error generating SAS URL: {e}")
        raise Exception(f"Failed to generate secure access URL: {str(e)}")


@heatmaps_router.get(
    path="/get_heatmaps",
    auth=[JWTAuth(), django_auth],
    response=HeatmapSchema
)
def get_heatmap_url(request, farm_id: str, index_type: str, sensed_date: str):
    """Get heatmap URL from storage with secure SAS token"""
    try:
        farm = Farm.objects.get(field_id=farm_id)
    except Farm.DoesNotExist:
        raise HttpError(400, "farm not found")
    
    try:
        date_obj = datetime.strptime(sensed_date, "%Y%m%d").date()
    except ValueError:
        raise HttpError(400, "Invalid date format. Expected YYYYMMDD.")
    
    heatmap = Heatmap.objects.filter(
        farm=farm,
        index_type=index_type,
        date=date_obj
    ).first()
    
    if not heatmap:
        raise HttpError(400, "heatmap not found")
    
    # Generate secure SAS URL (valid for 1 hour)
    try:
        secure_url = generate_sas_url(heatmap.image_url, expiry_minutes=60)
    except FileNotFoundError:
        raise HttpError(404, "Heatmap image not found in storage")
    except Exception as e:
        raise HttpError(500, f"Failed to generate access URL: {str(e)}")
    
    return {
        "farm_id": farm_id,
        "index_type": index_type,
        "date": date_obj,
        "image_url": secure_url,
        "expires_at": (datetime.utcnow() + timedelta(minutes=60)).isoformat() + "Z"
    }

@heatmaps_router.get(
    path="/get_past_satellite_values",
    response=IndexTimeSeriesResponseSchema
)
def get_past_satellite_data(request, farm_id : str, index_type : str):
    """Return satellite index values (with dates) for the last 30 days"""
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)
    try:
        farm = Farm.objects.get(field_id=farm_id)
    except Farm.DoesNotExist:
        raise HttpError(400, "farm not found")
    queryset = (
        IndexTimeSeries.objects
        .filter(
            farm=farm,
            index_type=index_type,
            date__gte=thirty_days_ago,
            date__lte=today
        )
        .order_by("date")
        .values("date", "value")
    )

    data = [IndexValueDateSchema(**entry) for entry in queryset]

    return {
        "farm_id": farm_id,
        "index_type": index_type,
        "data": data
    }
    
@heatmaps_router.get(
    path="/get_one_past_satellite_value",
    response=IndexValueDateResponseSchema
)
def get_past_satellite_data_for_one_day(request, farm_id : str, index_type : str, date : str):
    """Return satellite index values (with dates) for the last 30 days"""
    try:
        farm = Farm.objects.get(field_id=farm_id)
    except Farm.DoesNotExist:
        raise HttpError(400, "farm not found")
    queryset = (
        IndexTimeSeries.objects.filter(
            farm=farm,
            index_type=index_type,
            date = date
        )
    ).first()

    return {
        "farm_id": farm_id,
        "index_type": index_type,
        "data": queryset.value if queryset.value else None
    }