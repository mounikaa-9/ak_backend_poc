from datetime import datetime, timezone

from users.models import Farm
from ai_advisory.models import Advisory

def save_ai_adviosry_from_response(api_response : dict, field_id : str):
    """
    Create Advisory from API response
    
    Args:
        api_response (dict): The API response JSON
        farm: Field Id
    
    Returns:
        Advisory: Created Advisory instance
    """
    # Parse dates
    sowing_date = datetime.strptime(api_response['SowingDate'], '%Y%m%d').date()
    sensed_day = datetime.strptime(api_response['SensedDay'], '%Y%m%d').date()
    
    # Extract field area value
    field_area_str = api_response['fieldArea']
    field_area = float(field_area_str.split()[0]) if ' ' in field_area_str else float(field_area_str)
    
    farm = Farm.objects.get(
        field_id = field_id
    )
    
    return Advisory.objects.create(
        farm=farm,
        field_id=api_response.get('fieldID'),
        field_name=api_response.get('fieldName', ''),
        field_area=field_area if field_area is not None else 0,
        field_area_unit='acres',
        crop=api_response.get('Crop'),
        sowing_date=sowing_date if sowing_date else timezone.now().date(),
        timestamp=api_response.get('timestamp', int(timezone.now().timestamp())),
        sar_day=api_response.get('SARDay', ''),
        sensed_day=sensed_day if sensed_day else timezone.now().date(),
        last_satellite_visit=api_response.get('lastSatelliteVisit', ''),
        satellite_data=api_response.get('Satellite_Data', {}),
        advisory_data=api_response.get('advisory', {}),
        raw_response=api_response if api_response else {}
    )