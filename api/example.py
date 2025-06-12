from fastapi import FastAPI, HTTPException
from config.database import get_database, connect_and_check_db
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str

@app.on_event("startup")
async def startup_db_client():
    await connect_and_check_db()

@app.post("/items/")
async def create_item(item: Item):
    try:
        db = get_database()
        result = await db.items.insert_one(item.dict())
        return {"id": str(result.inserted_id), **item.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/items/")
async def get_items():
    try:
        db = get_database()
        items = await db.items.find().to_list(length=100)
        return [{"id": str(item["_id"]), "name": item["name"], "description": item["description"]} for item in items]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 