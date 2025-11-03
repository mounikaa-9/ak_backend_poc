from typing import Optional
from datetime import date
from ninja import Schema

class CropLossAnalyticsResponseSchema(Schema):
    """Crop Loss Analytics API call schema"""
    start_date : Optional[date]
    approx_end_date : Optional[date]
    kind : str