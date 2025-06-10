from datetime import datetime
from fastapi import FastAPI, HTTPException
from typing import Dict, List
import json

from ..data_models import GeoparkData, MarketCapData, BrentData, DailyReport
from ..data_storage import DataStorage

app = FastAPI()
storage = DataStorage()

@app.get("/api/data/latest")
async def get_latest_data():
    """Obtiene los datos más recientes de todas las fuentes"""
    try:
        # Simulación de datos de ejemplo
        current_date = datetime.now()
        
        # Datos de GeoPark
        geopark_data = GeoparkData(
            date=current_date,
            production=15000.0,  # barriles por día
            revenue=750000.0,    # USD
            wells=45,
            location="Colombia - Llanos",
            status="Operativo"
        )
        
        # Datos de Market Cap
        market_data = MarketCapData(
            date=current_date,
            stock_price=12.45,
            market_cap=750000000.0,
            volume=125000,
            currency="USD"
        )
        
        # Datos del Brent
        brent_data = BrentData(
            date=current_date,
            price=85.45,
            volume=1500000,
            change=0.25
        )
        
        # Crear reporte diario
        daily_report = DailyReport(
            date=current_date,
            geopark_data=geopark_data,
            market_data=market_data,
            brent_data=brent_data,
            summary="Operaciones normales, producción dentro de lo esperado",
            alerts=[]
        )
        
        # Almacenar todos los datos
        storage.save_geopark_data(geopark_data)
        storage.save_market_data(market_data)
        storage.save_brent_data(brent_data)
        storage.save_daily_report(daily_report)
        
        return {
            "status": "success",
            "data": {
                "geopark": {
                    "production": geopark_data.production,
                    "revenue": geopark_data.revenue,
                    "wells": geopark_data.wells,
                    "location": geopark_data.location,
                    "status": geopark_data.status
                },
                "market": {
                    "stock_price": market_data.stock_price,
                    "market_cap": market_data.market_cap,
                    "volume": market_data.volume,
                    "currency": market_data.currency
                },
                "brent": {
                    "price": brent_data.price,
                    "volume": brent_data.volume,
                    "change": brent_data.change
                }
            },
            "timestamp": current_date.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data/{data_type}/{year}/{month}/{day}")
async def get_historical_data(data_type: str, year: int, month: int, day: int):
    """Obtiene datos históricos por tipo y fecha"""
    try:
        date_path = f"{year}/{month:02d}/{day:02d}"
        base_path = f"data/{data_type}/{date_path}/data.json"
        
        with open(base_path, "r") as f:
            data = json.load(f)
        
        return {
            "status": "success",
            "data": data,
            "data_type": data_type,
            "date": f"{year}-{month:02d}-{day:02d}"
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, 
            detail=f"No data found for {data_type} on {year}-{month:02d}-{day:02d}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 