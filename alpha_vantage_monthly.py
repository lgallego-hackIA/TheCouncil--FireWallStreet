import asyncio
import aiohttp
import json
from datetime import datetime
from config.database import get_database, connect_and_check_db, close_db_connection

class AlphaVantageMonthly:
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.council_data
        self.api_key = "31FP79GBN03HSLJA"  # Tu API key de Alpha Vantage
        self.base_url = "https://www.alphavantage.co/query"

    async def fetch_monthly_data(self, symbol="GPRK"):
        """Obtiene datos mensuales desde Alpha Vantage"""
        params = {
            "function": "TIME_SERIES_MONTHLY",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "Error Message" in data:
                            print(f"Error de API: {data['Error Message']}")
                            return None
                        return data
                    else:
                        print(f"Error en la solicitud: {response.status}")
                        return None
        except Exception as e:
            print(f"Error al obtener datos de Alpha Vantage: {e}")
            return None

    async def process_monthly_data(self, raw_data):
        """Procesa los datos mensuales para un formato más manejable"""
        if not raw_data or "Monthly Time Series" not in raw_data:
            return None

        monthly_data = raw_data["Monthly Time Series"]
        processed_data = []

        for date, values in monthly_data.items():
            processed_data.append({
                "date": date,
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"]),
                "volume": int(values["5. volume"])
            })

        return sorted(processed_data, key=lambda x: x["date"])

    async def save_monthly_data(self, symbol, processed_data):
        """Guarda los datos mensuales en MongoDB"""
        if not processed_data:
            return False

        monthly_record = {
            "type": "monthly_stock_history",
            "symbol": symbol,
            "last_updated": datetime.now(),
            "data": processed_data
        }

        try:
            # Actualizar el documento existente con los datos mensuales
            result = await self.collection.update_one(
                {"id": "1000"},
                {
                    "$set": {
                        "monthly_stock_data": monthly_record
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error al guardar en MongoDB: {e}")
            return False

    async def generate_monthly_summary(self, processed_data):
        """Genera un resumen de los datos mensuales"""
        if not processed_data:
            return None

        closing_prices = [record["close"] for record in processed_data]
        monthly_volumes = [record["volume"] for record in processed_data]

        return {
            "total_months": len(processed_data),
            "latest_close": processed_data[-1]["close"],
            "highest_close": max(closing_prices),
            "lowest_close": min(closing_prices),
            "average_close": sum(closing_prices) / len(closing_prices),
            "average_volume": sum(monthly_volumes) / len(monthly_volumes),
            "first_date": processed_data[0]["date"],
            "last_date": processed_data[-1]["date"]
        }

async def main():
    print("=== Sistema de Registro de Datos Mensuales de Alpha Vantage ===\n")
    
    # Inicializar conexión a MongoDB
    connection_success = await connect_and_check_db()
    if not connection_success:
        print("Error: No se pudo conectar a MongoDB")
        return

    service = AlphaVantageMonthly()
    symbol = "GPRK"  # Símbolo de GeoPark
    
    # 1. Obtener datos mensuales
    print(f"1. Obteniendo datos mensuales para {symbol}...")
    raw_data = await service.fetch_monthly_data(symbol)
    
    if raw_data:
        # 2. Procesar datos
        print("\n2. Procesando datos mensuales...")
        processed_data = await service.process_monthly_data(raw_data)
        
        if processed_data:
            print(f"✓ Datos procesados: {len(processed_data)} registros mensuales")
            
            # 3. Guardar en MongoDB
            print("\n3. Guardando datos en MongoDB...")
            success = await service.save_monthly_data(symbol, processed_data)
            if success:
                print("✓ Datos guardados exitosamente")
                
                # 4. Generar resumen
                print("\n4. Generando resumen estadístico...")
                summary = await service.generate_monthly_summary(processed_data)
                if summary:
                    print("\nResumen de Datos Mensuales:")
                    print(f"Período analizado: {summary['first_date']} a {summary['last_date']}")
                    print(f"Total de meses: {summary['total_months']}")
                    print(f"Último precio de cierre: ${summary['latest_close']:.2f}")
                    print(f"Precio más alto: ${summary['highest_close']:.2f}")
                    print(f"Precio más bajo: ${summary['lowest_close']:.2f}")
                    print(f"Precio promedio: ${summary['average_close']:.2f}")
                    print(f"Volumen promedio: {summary['average_volume']:,.0f}")
            else:
                print("✗ Error al guardar datos")
        else:
            print("✗ Error al procesar datos")
    else:
        print("✗ Error al obtener datos de Alpha Vantage")
    
    await close_db_connection()

if __name__ == "__main__":
    asyncio.run(main()) 