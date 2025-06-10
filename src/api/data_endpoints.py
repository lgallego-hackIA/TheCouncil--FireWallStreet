from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from ..data_models import GeoparkData, MarketCapData, BrentData, DailyReport
from ..data_storage import DataStorage

router = APIRouter()
storage = DataStorage()

@router.post("/geopark")
async def save_geopark_data(data: dict):
    try:
        geopark_data = GeoparkData(
            date=datetime.fromisoformat(data.get('date')),
            production=float(data.get('production', 0)),
            revenue=float(data.get('revenue', 0)),
            wells=int(data.get('wells', 0)),
            location=str(data.get('location', '')),
            status=str(data.get('status', 'active'))
        )
        storage.save_geopark_data(geopark_data)
        return {"message": "Datos de GeoPark guardados exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/market")
async def save_market_data(data: dict):
    try:
        market_data = MarketCapData(
            date=datetime.fromisoformat(data.get('date')),
            stock_price=float(data.get('stock_price', 0)),
            market_cap=float(data.get('market_cap', 0)),
            volume=int(data.get('volume', 0)),
            currency=str(data.get('currency', 'USD'))
        )
        storage.save_market_data(market_data)
        return {"message": "Datos de Market Cap guardados exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/brent")
async def save_brent_data(data: dict):
    try:
        brent_data = BrentData(
            date=datetime.fromisoformat(data.get('date')),
            price=float(data.get('price', 0)),
            volume=int(data.get('volume', 0)),
            change=float(data.get('change', 0))
        )
        storage.save_brent_data(brent_data)
        return {"message": "Datos del Brent guardados exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/daily-report/{date}")
async def get_daily_report(date: str):
    try:
        report_date = datetime.fromisoformat(date)
        # Aquí implementarías la lógica para recuperar el reporte diario
        # Por ahora retornamos un ejemplo
        return {
            "date": date,
            "status": "success",
            "message": f"Reporte para la fecha {date}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 