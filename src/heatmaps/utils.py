import os
import django
import json
from datetime import datetime
from django.db import transaction
from heatmaps.models import Heatmap, IndexTimeSeries
from users.models import Farm

def save_heatmaps_from_response(field_data: dict):
    """
    Save satellite index image URLs into the Heatmap model.

    Args:
        field_data (dict): JSON response containing satellite URLs and metadata.
    Raises:
        ValueError: If required metadata is missing or invalid.
        Farm.DoesNotExist: If the specified farm is not found.
    """
    meta = field_data.get('_meta', {})
    field_id = meta.get('field_id')
    sensed_day = meta.get('sensed_day')

    if not field_id:
        raise ValueError("Missing 'field_id' in field_data['_meta']")
    if not sensed_day:
        raise ValueError("Missing 'sensed_day' in field_data['_meta']")

    try:
        sensed_date = datetime.strptime(sensed_day, "%Y%m%d").date()
    except Exception:
        raise ValueError(f"Invalid 'sensed_day' format: {sensed_day}. Expected YYYYMMDD.")

    farm = Farm.objects.get(field_id=field_id)

    with transaction.atomic():
        for index_type, url in field_data.items():
            if index_type == "_meta" or not url:
                continue

            if index_type not in dict(Heatmap.INDEX_CHOICES):
                continue
                # raise ValueError(f"Unrecognized index type: {index_type}")

            Heatmap.objects.update_or_create(
                farm=farm,
                index_type=index_type,
                date=sensed_date,
                defaults={"image_url": url},
            )
            
def save_index_values_from_response(field_data : dict):
    
    meta = field_data.get('_meta', {})
    field_id = meta.get('field_id')
    sensed_day = meta.get('sensed_day')
    
    if not field_id:
        raise ValueError("Missing 'field_id' in field_data['_meta']")
    if not sensed_day:
        raise ValueError("Missing 'sensed_day' in field_data['_meta']")

    try:
        sensed_date = datetime.strptime(sensed_day, "%Y%m%d").date()
    except Exception:
        raise ValueError(f"Invalid 'sensed_day' format: {sensed_day}. Expected YYYYMMDD.")

    farm = Farm.objects.get(field_id=field_id)

    with transaction.atomic():
        for index_type, value in field_data.items():
            if index_type == "_meta" or not value:
                continue

            if index_type not in dict(IndexTimeSeries.INDEX_CHOICES):
                continue
            
            if value == -1:
                value = None

            IndexTimeSeries.objects.update_or_create(
                farm=farm,
                index_type=index_type,
                date=sensed_date,
                defaults={"value": value},
            )
    
if __name__ == "__main__":
    with open('field_1761808284616_20251029.json', 'r') as f:
        data = json.load(f)
    save_heatmaps_from_response(
        field_data = data
    )