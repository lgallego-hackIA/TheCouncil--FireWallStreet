import os
import requests
from datetime import datetime
from typing import Dict, Optional
from ..data_models import MarketCapData
from ..config import get_settings
import aiohttp
import json

class AlphaVantageService:
    def __init__(self):
        self.api_key = get_settings().alpha_vantage_api_key
        self.base_url = "https://www.alphavantage.co/query"

    async def get_stock_data(self, symbol: str = "GEO"):
        """
        Obtiene datos de la acción de GeoPark (GPRK) desde Alpha Vantage
        """
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params) as response:
                data = await response.json()
                return data

    async def get_price_history(self, symbol: str = "GEO"):
        """
        Obtiene precios históricos diarios
        """
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, params=params) as response:
                data = await response.json()
                return data 