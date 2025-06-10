from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from ..data_models import GeoparkData, MarketCapData, BrentData, DailyReport
from ..data_storage import DataStorage
from ..services.alpha_vantage import AlphaVantageService
from ..config import get_settings

router = APIRouter()
storage = DataStorage()

async def get_alpha_vantage_service():
    settings = get_settings()
    if not settings.ALPHA_VANTAGE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Alpha Vantage API key not configured"
        )
    return AlphaVantageService(settings.ALPHA_VANTAGE_API_KEY)

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
async def save_market_data(
    alpha_vantage: AlphaVantageService = Depends(get_alpha_vantage_service)
):
    """
    Obtiene y guarda datos del mercado usando Alpha Vantage
    """
    try:
        # Obtener datos de Alpha Vantage
        market_data = await alpha_vantage.get_stock_data()
        
        # Guardar datos
        storage.save_market_data(market_data)
        
        return {
            "message": "Datos de Market Cap guardados exitosamente",
            "data": {
                "stock_price": market_data.stock_price,
                "market_cap": market_data.market_cap,
                "volume": market_data.volume,
                "currency": market_data.currency
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/market/history")
async def get_market_history(
    alpha_vantage: AlphaVantageService = Depends(get_alpha_vantage_service)
):
    """
    Obtiene el historial de precios de la acción
    """
    try:
        history = await alpha_vantage.get_daily_prices()
        return history
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
        return {
            "date": date,
            "status": "success",
            "message": f"Reporte para la fecha {date}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 