"""
Domain models for inventory automation.
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# TODO: Define your domain models here
class InventoryItem(BaseModel):
    """Example domain model for inventory."""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
