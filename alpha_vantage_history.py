import asyncio
from datetime import datetime
from config.database import get_database, connect_and_check_db, close_db_connection
import requests
import json

class AlphaVantageHistory:
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.council_data
        self.api_endpoint = "https://geopark-financial-api.onrender.com/api/geopark/stock-price"

    async def fetch_stock_data(self, symbol="GPRK"):
        """Obtiene datos de la acción desde la API"""
        try:
            response = requests.get(self.api_endpoint, params={"symbol": symbol})
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error al obtener datos de la API: {e}")
            return None

    async def record_stock_history(self, stock_data):
        """Registra el historial de precios en MongoDB"""
        if not stock_data:
            return False

        history_record = {
            "type": "stock_price_history",
            "timestamp": datetime.now(),
            "symbol": stock_data.get("symbol"),
            "price": stock_data.get("price"),
            "change": stock_data.get("change"),
            "change_percent": stock_data.get("change_percent"),
            "trading_date": stock_data.get("trading_date"),
            "source": stock_data.get("source")
        }

        try:
            # Actualizar el documento existente agregando al historial
            result = await self.collection.update_one(
                {"id": "1000"},  # Documento principal del consejo
                {
                    "$push": {
                        "stock_price_history": history_record
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error al guardar en MongoDB: {e}")
            return False

    async def get_price_history(self):
        """Obtiene el historial de precios almacenado"""
        try:
            document = await self.collection.find_one({"id": "1000"})
            if document and "stock_price_history" in document:
                return document["stock_price_history"]
            return []
        except Exception as e:
            print(f"Error al obtener historial: {e}")
            return []

    async def generate_price_summary(self):
        """Genera un resumen del historial de precios"""
        history = await self.get_price_history()
        if not history:
            return None

        prices = [float(record["price"]) for record in history]
        
        summary = {
            "total_records": len(history),
            "latest_price": history[-1]["price"] if history else None,
            "average_price": sum(prices) / len(prices) if prices else 0,
            "max_price": max(prices) if prices else 0,
            "min_price": min(prices) if prices else 0,
            "first_record_date": history[0]["timestamp"] if history else None,
            "last_record_date": history[-1]["timestamp"] if history else None
        }
        return summary

async def main():
    print("=== Sistema de Registro Histórico de Precios de Acciones ===\n")
    
    # Inicializar conexión a MongoDB
    connection_success = await connect_and_check_db()
    if not connection_success:
        print("Error: No se pudo conectar a MongoDB")
        return

    history_service = AlphaVantageHistory()
    
    # 1. Obtener datos actuales
    print("1. Obteniendo datos actuales de la acción...")
    stock_data = await history_service.fetch_stock_data()
    if stock_data:
        print(f"Datos obtenidos para {stock_data.get('symbol')}:")
        print(f"Precio: ${stock_data.get('price')}")
        print(f"Cambio: {stock_data.get('change')} ({stock_data.get('change_percent')})")
        
        # 2. Registrar en el historial
        print("\n2. Registrando datos en el historial...")
        success = await history_service.record_stock_history(stock_data)
        if success:
            print("✓ Datos registrados exitosamente")
        else:
            print("✗ Error al registrar datos")
    
    # 3. Obtener historial completo
    print("\n3. Obteniendo historial de precios...")
    history = await history_service.get_price_history()
    print(f"Registros encontrados: {len(history)}")
    
    if history:
        print("\nÚltimos 5 registros:")
        for record in history[-5:]:
            print(f"- {record['timestamp']}: ${record['price']} ({record['change_percent']})")
    
    # 4. Generar resumen
    print("\n4. Generando resumen estadístico...")
    summary = await history_service.generate_price_summary()
    if summary:
        print("\nResumen del Historial:")
        print(f"Total de registros: {summary['total_records']}")
        print(f"Precio más reciente: ${summary['latest_price']}")
        print(f"Precio promedio: ${summary['average_price']:.2f}")
        print(f"Precio más alto: ${summary['max_price']}")
        print(f"Precio más bajo: ${summary['min_price']}")
        print(f"Primer registro: {summary['first_record_date']}")
        print(f"Último registro: {summary['last_record_date']}")
    
    await close_db_connection()

if __name__ == "__main__":
    asyncio.run(main()) 