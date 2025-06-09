"""
Domain models for products automation.
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# TODO: Define your domain models here
class ProductsItem(BaseModel):
    """Example domain model for products."""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
