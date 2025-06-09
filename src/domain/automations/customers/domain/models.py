"""
Domain models for customers automation.
"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# TODO: Define your domain models here
class CustomersItem(BaseModel):
    """Example domain model for customers."""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
