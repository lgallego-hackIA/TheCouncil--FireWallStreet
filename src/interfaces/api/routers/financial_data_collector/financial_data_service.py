"""
Servicio para procesar y almacenar datos financieros.
"""
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from .alpha_vantage_client import AlphaVantageClient # MODIFIED IMPORT

try:
    from src.infrastructure.storage.blob_storage import BlobStorageAdapter
    BLOB_STORAGE_AVAILABLE = True
except ImportError:
    logging.warning("Vercel Blob Storage no disponible. Se usará respaldo local.")
    BLOB_STORAGE_AVAILABLE = False

logger = logging.getLogger(__name__)

class FinancialDataService:
    """
    Servicio para procesar y almacenar datos financieros.
    Utiliza Alpha Vantage para obtener datos y Vercel Blob Storage para almacenarlos.
    """
    
    DATA_FILE_PATH = "data/automations/financial_data_collector_data.json" # MODIFIED DATA_FILE_PATH
    
    def __init__(self):
        """Inicializa el servicio de datos financieros."""
        self.alpha_vantage_client = AlphaVantageClient()
        # os.makedirs removed as it's not suitable for Vercel's read-only filesystem
    
    async def get_stock_price(self, symbol: str = "GPRK") -> Dict[str, Any]:
        """
        Obtiene el precio actual de una acción.
        
        Args:
            symbol: El símbolo de la acción (por defecto: GPRK)
            
        Returns:
            Datos del precio de la acción
        """
        try:
            logger.info(f"Obteniendo datos de precio para {symbol} desde Alpha Vantage")
            quote_data = await self.alpha_vantage_client.get_stock_quote(symbol)
            logger.debug(f"Datos recibidos de Alpha Vantage: {quote_data}")
            
            if "Global Quote" in quote_data:
                price_data = {
                    "symbol": symbol,
                    "price": quote_data["Global Quote"].get("05. price", "N/A"),
                    "change": quote_data["Global Quote"].get("09. change", "N/A"),
                    "change_percent": quote_data["Global Quote"].get("10. change percent", "N/A"),
                    "timestamp": datetime.now().isoformat(),
                    "source": "Alpha Vantage"
                }
                await self._save_financial_data(f"stock_price_{symbol}", price_data)
                return price_data
            else:
                logger.error(f"Datos de precio no disponibles para {symbol}. Respuesta: {quote_data}")
                return {"error": f"Datos de precio no disponibles para {symbol}"}
        except Exception as e:
            logger.exception(f"Error en get_stock_price para {symbol}: {str(e)}")
            return {"error": f"Error al obtener precio de acción: {str(e)}"}
    
    async def get_brent_price(self) -> Dict[str, Any]:
        """
        Obtiene el precio actual del petróleo Brent.
        Si no hay datos actuales, intenta obtener datos históricos.
        
        Returns:
            Datos del precio del Brent
        """
        try:
            logger.info("Obteniendo datos de precio del Brent desde Alpha Vantage")
            brent_data = await self.alpha_vantage_client.get_brent_price()
            logger.debug(f"Datos recibidos de Alpha Vantage: {brent_data}")
            
            if "Global Quote" in brent_data and brent_data["Global Quote"].get("05. price"):
                symbol = brent_data["Global Quote"].get("01. symbol", "BRENT")
                is_historical = "source" in brent_data["Global Quote"] and "Historical" in brent_data["Global Quote"]["source"]
                price_data = {
                    "symbol": symbol,
                    "price": brent_data["Global Quote"].get("05. price", "N/A"),
                    "change": brent_data["Global Quote"].get("09. change", "N/A"),
                    "change_percent": brent_data["Global Quote"].get("10. change percent", "N/A"),
                    "timestamp": datetime.now().isoformat(),
                    "source": "Alpha Vantage" if not is_historical else brent_data["Global Quote"]["source"],
                    "trading_date": brent_data["Global Quote"].get("07. latest trading day", datetime.now().strftime("%Y-%m-%d"))
                }
                await self._save_financial_data("brent_price", price_data)
                return price_data
            elif "error" in brent_data:
                logger.warning(f"Error al obtener datos del Brent: {brent_data['error']}")
                logger.info("Intentando recuperar datos previos almacenados")
                previous_data = await self._load_previous_data("brent_price")
                if previous_data:
                    logger.info(f"Usando datos previos para el precio del Brent: {previous_data.get('price')}")
                    previous_data["timestamp"] = datetime.now().isoformat()
                    if "source" not in previous_data:
                        previous_data["source"] = "Alpha Vantage (from previous execution)"
                    return previous_data
                else:
                    return brent_data
            else:
                logger.error(f"Formato de datos inesperado para el Brent: {brent_data}")
                return {"error": "Formato de datos inesperado para el Brent"}
        except Exception as e:
            logger.exception(f"Error en get_brent_price: {str(e)}")
            previous_data = await self._load_previous_data("brent_price")
            if previous_data:
                logger.info(f"Usando datos previos para el precio del Brent debido a un error: {previous_data.get('price')}")
                previous_data["timestamp"] = datetime.now().isoformat()
                if "source" not in previous_data:
                    previous_data["source"] = "Alpha Vantage (from previous execution)"
                return previous_data
            else:
                return {"error": f"Error al obtener precio de Brent y no hay datos históricos disponibles: {str(e)}"}
    
    async def get_trading_volume(self, symbol: str = "GPRK") -> Dict[str, Any]:
        """
        Obtiene el volumen de transacciones de una acción.
        
        Args:
            symbol: El símbolo de la acción (por defecto: GPRK)
            
        Returns:
            Datos del volumen de transacciones
        """
        try:
            logger.info(f"Obteniendo datos de volumen para {symbol} desde Alpha Vantage")
            quote_data = await self.alpha_vantage_client.get_stock_quote(symbol)
            logger.debug(f"Datos recibidos de Alpha Vantage: {quote_data}")
            
            if "Global Quote" in quote_data:
                volume_data = {
                    "symbol": symbol,
                    "volume": quote_data["Global Quote"].get("06. volume", "N/A"),
                    "timestamp": datetime.now().isoformat(),
                    "source": "Alpha Vantage"
                }
                await self._save_financial_data(f"trading_volume_{symbol}", volume_data)
                return volume_data
            else:
                logger.error(f"Datos de volumen no disponibles para {symbol}. Respuesta: {quote_data}")
                return {"error": f"Datos de volumen no disponibles para {symbol}"}
        except Exception as e:
            logger.exception(f"Error en get_trading_volume para {symbol}: {str(e)}")
            return {"error": f"Error al obtener volumen de transacciones: {str(e)}"}
    
    async def get_market_cap(self, symbol: str = "GPRK") -> Dict[str, Any]:
        """
        Obtiene la capitalización de mercado de una empresa.
        
        Args:
            symbol: El símbolo de la acción (por defecto: GPRK)
            
        Returns:
            Datos de capitalización de mercado
        """
        try:
            logger.info(f"Obteniendo datos de capitalización de mercado para {symbol} desde Alpha Vantage")
            overview_data = await self.alpha_vantage_client.get_company_overview(symbol)
            logger.debug(f"Datos recibidos de Alpha Vantage: {overview_data}")
            
            if "MarketCapitalization" in overview_data:
                market_cap_data = {
                    "symbol": symbol,
                    "market_cap": overview_data.get("MarketCapitalization", "N/A"),
                    "name": overview_data.get("Name", symbol),
                    "sector": overview_data.get("Sector", "N/A"),
                    "industry": overview_data.get("Industry", "N/A"),
                    "timestamp": datetime.now().isoformat(),
                    "source": "Alpha Vantage"
                }
                await self._save_financial_data(f"market_cap_{symbol}", market_cap_data)
                return market_cap_data
            else:
                logger.error(f"Datos de capitalización de mercado no disponibles para {symbol}. Respuesta: {overview_data}")
                return {"error": f"Datos de capitalización de mercado no disponibles para {symbol}"}
        except Exception as e:
            logger.exception(f"Error en get_market_cap para {symbol}: {str(e)}")
            return {"error": f"Error al obtener capitalización de mercado: {str(e)}"}
    
    async def get_all_financial_data(self, symbol: str = "GPRK") -> Dict[str, Any]:
        """
        Obtiene todos los datos financieros en una sola llamada.
        
        Args:
            symbol: El símbolo de la acción (por defecto: GPRK)
            
        Returns:
            Todos los datos financieros
        """
        try:
            logger.info(f"Obteniendo todos los datos financieros para {symbol}")
            stock_price = await self.get_stock_price(symbol)
            brent_price = await self.get_brent_price()
            trading_volume = await self.get_trading_volume(symbol)
            market_cap = await self.get_market_cap(symbol)
            
            all_data = {
                "stock_price": stock_price,
                "brent_price": brent_price,
                "trading_volume": trading_volume,
                "market_cap": market_cap,
                "timestamp": datetime.now().isoformat()
            }
            await self._save_financial_data(f"all_financial_data_{symbol}", all_data)
            return all_data
        except Exception as e:
            logger.exception(f"Error en get_all_financial_data para {symbol}: {str(e)}")
            return {"error": f"Error al obtener todos los datos financieros: {str(e)}"}
    
    async def _load_previous_data(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Carga datos financieros previos desde el almacenamiento local.
        
        Args:
            key: Clave para identificar los datos (ej: 'brent_price')
            
        Returns:
            Datos financieros previos o None si no existen
        """
        try:
            if os.path.exists(self.DATA_FILE_PATH):
                logger.info(f"Buscando datos previos para '{key}' en {self.DATA_FILE_PATH}")
                with open(self.DATA_FILE_PATH, 'r') as f:
                    data = json.load(f)
                
                if isinstance(data, dict) and data.get("symbol") is not None:
                    if key.endswith(data.get("symbol", "")) or key == "brent_price" and data.get("symbol") in ["BRENT", "BZ", "UKOIL"]:
                        logger.info(f"Encontrados datos previos para '{key}'")
                        return data
                
                if key == "brent_price" and "brent_price" in data:
                    logger.info(f"Encontrados datos previos para 'brent_price' en datos combinados")
                    return data["brent_price"]
                
                logger.warning(f"No se encontraron datos para '{key}' en el archivo")
            else:
                logger.warning(f"El archivo de datos {self.DATA_FILE_PATH} no existe")
            return None
        except Exception as e:
            logger.exception(f"Error al cargar datos previos para '{key}': {str(e)}")
            return None
    
    async def _save_financial_data(self, key: str, data: Dict[str, Any]) -> Optional[str]:
        """
        Guarda datos financieros en almacenamiento.
        Utiliza Vercel Blob Storage si está disponible, de lo contrario, registra un mensaje.
        
        Args:
            key: Clave para identificar los datos
            data: Datos a guardar
            
        Returns:
            URL de almacenamiento si está disponible, None en caso contrario
        """
        try:
            if BLOB_STORAGE_AVAILABLE and BlobStorageAdapter.is_available():
                url = await BlobStorageAdapter.save_json(key, data, folder="financial_data_collector")
                logger.info(f"Datos financieros guardados en Blob Storage: {url}")
                return url
            else:
                # Fallback to local file system is not suitable for Vercel's read-only environment
                # if BlobStorageAdapter was expected to be available.
                if BLOB_STORAGE_AVAILABLE: # i.e. import BlobStorageAdapter succeeded
                    logger.critical(
                        "Vercel Blob Storage was expected but BlobStorageAdapter.is_available() returned False. "
                        "Data cannot be saved to blob storage. Check vercel_blob import and initialization in blob_storage.py. "
                        "NOT attempting local file save on Vercel."
                    )
                else: # BlobStorageAdapter itself could not be imported
                    logger.warning(
                        "Vercel Blob Storage (BlobStorageAdapter) import failed. "
                        "Data cannot be saved to blob storage. NOT attempting local file save on Vercel."
                    )
                # To make it explicit that saving failed because blob storage isn't working as expected:
                # raise RuntimeError("Failed to save data: Blob Storage unavailable or not functioning.")
                return None # Indicate failure to save
        except Exception as e:
            logger.exception(f"Error al guardar datos financieros: {str(e)}")
            return None
