from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict

@dataclass
class GeoparkData:
    date: datetime
    production: float  # Producción diaria en barriles
    revenue: float    # Ingresos
    wells: int        # Número de pozos activos
    location: str     # Ubicación/Campo
    status: str       # Estado operativo

@dataclass
class MarketCapData:
    date: datetime
    stock_price: float      # Precio de la acción
    market_cap: float       # Capitalización de mercado
    volume: int            # Volumen de transacciones
    currency: str          # Moneda (USD, etc.)

@dataclass
class BrentData:
    date: datetime
    price: float           # Precio del Brent
    volume: int           # Volumen de transacciones
    change: float         # Cambio porcentual

@dataclass
class DailyReport:
    date: datetime
    geopark_data: GeoparkData
    market_data: MarketCapData
    brent_data: BrentData
    summary: str
    alerts: List[str] 