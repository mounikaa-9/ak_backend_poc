from ninja import Schema
from typing import Any, Dict, List, Optional
from datetime import date

class AIAdvisoryItemSchema(Schema):
    id: int
    title: str
    description: str
    priority: str
    date: str

class AIAdvisoryResponseSchema(Schema):
    advisories: List[AIAdvisoryItemSchema]