from ninja import Schema, ModelSchema
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

class IndexTimeSeriesSchema(Schema):
    id: int
    farm_id: str
    index_type: str
    date: date
    value: Optional[Decimal]

class IndexTimeSeriesCreateSchema(Schema):
    farm_id: str
    index_type: str
    date: date
    value: Optional[Decimal]
    
class IndexTimeSeriesRequestSchema(Schema):
    farm_id: str
    index_type: str

class IndexValueDateSchema(Schema):
    date: date
    value: Optional[Decimal]
    
class IndexValueDateResponseSchema(Schema):
    date : date
    value : Optional[Decimal]
    index_type : str

class IndexTimeSeriesResponseSchema(Schema):
    """Time series data grouped by index type"""
    farm_id: str
    index_type: str
    data: List[IndexValueDateSchema]