from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class ActionRecord(BaseModel):
    action_id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    timestamp: datetime = Field(default_factory=datetime.now)
    action_type: str
    description: str
    user: str
    details: Dict[str, Any] = {}
    status: str = "completed"
    related_provider_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "action_type": "provider_update",
                "description": "Actualización de comités del proveedor",
                "user": "lgallego",
                "details": {
                    "previous_committees": ["C1", "C2"],
                    "new_committees": ["C1", "C2", "C3"]
                },
                "related_provider_id": "1"
            }
        } 