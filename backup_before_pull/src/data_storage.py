import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from .data_models import GeoparkData, MarketCapData, BrentData, DailyReport

class DataStorage:
    def __init__(self, base_path: str = "data"):
        self.base_path = base_path
        self._ensure_directories()

    def _ensure_directories(self):
        """Asegura que existan los directorios necesarios"""
        directories = [
            self.base_path,
            f"{self.base_path}/geopark",
            f"{self.base_path}/market",
            f"{self.base_path}/brent",
            f"{self.base_path}/reports"
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def _get_date_path(self, date: datetime) -> str:
        """Genera la estructura de directorios por fecha"""
        return f"{date.year}/{date.month:02d}/{date.day:02d}"

    def save_geopark_data(self, data: GeoparkData):
        """Almacena datos de GeoPark"""
        path = f"{self.base_path}/geopark/{self._get_date_path(data.date)}"
        os.makedirs(path, exist_ok=True)
        with open(f"{path}/data.json", "w") as f:
            json.dump({
                "date": data.date.isoformat(),
                "production": data.production,
                "revenue": data.revenue,
                "wells": data.wells,
                "location": data.location,
                "status": data.status
            }, f, indent=2)

    def save_market_data(self, data: MarketCapData):
        """Almacena datos de Market Cap"""
        path = f"{self.base_path}/market/{self._get_date_path(data.date)}"
        os.makedirs(path, exist_ok=True)
        with open(f"{path}/data.json", "w") as f:
            json.dump({
                "date": data.date.isoformat(),
                "stock_price": data.stock_price,
                "market_cap": data.market_cap,
                "volume": data.volume,
                "currency": data.currency
            }, f, indent=2)

    def save_brent_data(self, data: BrentData):
        """Almacena datos del Brent"""
        path = f"{self.base_path}/brent/{self._get_date_path(data.date)}"
        os.makedirs(path, exist_ok=True)
        with open(f"{path}/data.json", "w") as f:
            json.dump({
                "date": data.date.isoformat(),
                "price": data.price,
                "volume": data.volume,
                "change": data.change
            }, f, indent=2)

    def save_daily_report(self, report: DailyReport):
        """Almacena el reporte diario"""
        path = f"{self.base_path}/reports/{self._get_date_path(report.date)}"
        os.makedirs(path, exist_ok=True)
        with open(f"{path}/report.json", "w") as f:
            json.dump({
                "date": report.date.isoformat(),
                "geopark_data": {
                    "production": report.geopark_data.production,
                    "revenue": report.geopark_data.revenue,
                    "wells": report.geopark_data.wells,
                    "location": report.geopark_data.location,
                    "status": report.geopark_data.status
                },
                "market_data": {
                    "stock_price": report.market_data.stock_price,
                    "market_cap": report.market_data.market_cap,
                    "volume": report.market_data.volume,
                    "currency": report.market_data.currency
                },
                "brent_data": {
                    "price": report.brent_data.price,
                    "volume": report.brent_data.volume,
                    "change": report.brent_data.change
                },
                "summary": report.summary,
                "alerts": report.alerts
            }, f, indent=2) 