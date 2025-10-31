from ninja import Schema, ModelSchema
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

class HeatmapSchema(Schema):
    farm_id: str
    index_type: str
    date: date
    image_url: Optional[str]

class HeatmapCreateSchema(Schema):
    farm_id: str
    index_type: str
    date: date
    image_url: Optional[str]
    
class HeatmapURLSchema(Schema):
    farm_id : str
    index_type : str
    sensed_day : date
    
class HeatmapListSchema(Schema):
    heatmaps: List[HeatmapSchema]