from datetime import datetime

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
        field_id=api_response['fieldID'],
        field_name=api_response['fieldName'],
        field_area=field_area,
        field_area_unit='acres',
        crop=api_response['Crop'],
        sowing_date=sowing_date,
        timestamp=api_response['timestamp'],
        sar_day=api_response['SARDay'],
        sensed_day=sensed_day,
        last_satellite_visit=api_response['lastSatelliteVisit'],
        satellite_data=api_response['Satellite_Data'],
        advisory_data=api_response['advisory'],
        raw_response=api_response
    )