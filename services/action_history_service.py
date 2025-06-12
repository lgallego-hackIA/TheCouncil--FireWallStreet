from datetime import datetime, timedelta
from typing import List, Optional
from models.action_history import ActionRecord
from config.database import get_database

class ActionHistoryService:
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.action_history

    async def record_action(self, action: ActionRecord) -> str:
        """Registra una nueva acción en el historial"""
        result = await self.collection.insert_one(action.dict())
        return str(result.inserted_id)

    async def get_actions_by_date_range(
        self,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        action_type: Optional[str] = None,
        user: Optional[str] = None
    ) -> List[ActionRecord]:
        """Obtiene acciones dentro de un rango de fechas con filtros opcionales"""
        if end_date is None:
            end_date = datetime.now()

        query = {
            "timestamp": {
                "$gte": start_date,
                "$lte": end_date
            }
        }

        if action_type:
            query["action_type"] = action_type
        if user:
            query["user"] = user

        cursor = self.collection.find(query).sort("timestamp", -1)
        actions = await cursor.to_list(length=None)
        return [ActionRecord(**action) for action in actions]

    async def get_today_actions(self, user: Optional[str] = None) -> List[ActionRecord]:
        """Obtiene las acciones del día actual"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return await self.get_actions_by_date_range(today_start, user=user)

    async def get_last_n_days_actions(self, days: int, user: Optional[str] = None) -> List[ActionRecord]:
        """Obtiene las acciones de los últimos n días"""
        start_date = datetime.now() - timedelta(days=days)
        return await self.get_actions_by_date_range(start_date, user=user)

    async def get_actions_by_provider(self, provider_id: str) -> List[ActionRecord]:
        """Obtiene todas las acciones relacionadas con un proveedor específico"""
        cursor = self.collection.find({"related_provider_id": provider_id}).sort("timestamp", -1)
        actions = await cursor.to_list(length=None)
        return [ActionRecord(**action) for action in actions]

    async def get_action_summary(self, days: int = 30) -> dict:
        """Obtiene un resumen de las acciones realizadas"""
        start_date = datetime.now() - timedelta(days=days)
        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": {
                        "action_type": "$action_type",
                        "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}}
                    },
                    "count": {"$sum": 1},
                    "users": {"$addToSet": "$user"}
                }
            },
            {
                "$sort": {"_id.date": -1, "_id.action_type": 1}
            }
        ]
        
        results = await self.collection.aggregate(pipeline).to_list(length=None)
        return {
            "period": f"Últimos {days} días",
            "total_records": len(results),
            "actions_by_date": results
        } 