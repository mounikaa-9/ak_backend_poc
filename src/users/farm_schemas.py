from ninja import Schema
from typing import Optional, Dict, Any, List
from datetime import date, datetime

class FarmBaseSchema(Schema):
    """Shared fields across create and response schemas"""
    field_id: str
    farm_email : str
    field_name: str
    field_area: float
    crop: str
    sowing_date: date
    last_sensed_day: Optional[date]
    farm_coordinates: List[List[float]]
    
class FarmUpdateSchema(Schema):
    """Shared fields across create and response schemas"""
    field_id: str
    farm_email : str
    field_name: str
    field_area: float
    crop: str
    sowing_date: date
    last_sensed_day: Optional[date]
    farm_coordinates: List[List[float]]

class FarmCreateSchema(Schema):
    """Schema for creating a new farm"""
    farm_email : str
    field_name: str
    crop: str
    sowing_date: date
    farm_coordinates: List[List[float]]


class FarmUpdateSchema(Schema):
    """Schema for partial updates"""
    field_name: Optional[str] = None
    field_area: Optional[float] = None
    crop: Optional[str] = None
    sowing_date: Optional[date] = None
    last_sensed_day: Optional[date] = None
    farm_coordinates: Optional[List] = None

class FarmResponseSchema(Schema):
    """Schema for returning farm details"""
    field_id: str
    farm_email : str
    field_name: str
    field_area: float
    crop: str
    sowing_date: date
    last_sensed_day: Optional[date]
    farm_coordinates: List[List[float]]