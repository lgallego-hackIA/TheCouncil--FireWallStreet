import asyncio
import aiohttp
import json
from datetime import datetime
from statistics import mean

class AlphaVantageMonthly:
    def __init__(self):
        self.api_key = "31FP79GBN03HSLJA"
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

    async def calculate_average_share_price(self, raw_data, target_months=None):
        """Calcula el promedio del precio de las acciones para los meses especificados"""
        if not raw_data or "Monthly Time Series" not in raw_data:
            return None

        monthly_data = raw_data["Monthly Time Series"]
        share_prices = []
        filtered_prices = []

        print("\nPrecios mensuales de las acciones:")
        print("Fecha\t\tPrecio de Cierre")
        print("-" * 40)

        # Filtrar por los meses objetivo (marzo, abril y mayo 2025)
        target_months = ["2025-03", "2025-04", "2025-05"]
        
        for date, values in monthly_data.items():
            close_price = float(values["4. close"])
            share_prices.append((date, close_price))
            
            # Verificar si el mes actual está en los meses objetivo
            if any(date.startswith(target_month) for target_month in target_months):
                filtered_prices.append((date, close_price))
                print(f"{date}\t${close_price:.2f} *")  # Marcamos con * los meses objetivo
            else:
                print(f"{date}\t${close_price:.2f}")

        if filtered_prices:
            target_average = mean([price for _, price in filtered_prices])
            
            print("\nAnálisis del Período Marzo-Mayo 2025:")
            print("-" * 40)
            for date, price in filtered_prices:
                print(f"{date}: ${price:.2f}")
            print(f"\nPrecio promedio del período: ${target_average:.2f}")
            
            return {
                "period_dates": [date for date, _ in filtered_prices],
                "period_prices": [price for _, price in filtered_prices],
                "period_average": target_average
            }
        else:
            print("\nNo se encontraron datos para el período especificado")
            return None

async def main():
    print("=== Análisis de Precios de Acciones de GeoPark (Marzo-Mayo 2025) ===\n")
    
    service = AlphaVantageMonthly()
    symbol = "GPRK"  # Símbolo de GeoPark
    
    print(f"Obteniendo datos mensuales para {symbol}...")
    raw_data = await service.fetch_monthly_data(symbol)
    
    if raw_data:
        stats = await service.calculate_average_share_price(raw_data)
        if stats:
            print("\nResumen del período:")
            print(f"Fechas analizadas: {', '.join(stats['period_dates'])}")
            print(f"Promedio del período: ${stats['period_average']:.2f}")
            
            # Calcular variación porcentual
            prices = stats['period_prices']
            if len(prices) > 1:
                variation = ((prices[-1] - prices[0]) / prices[0]) * 100
                print(f"Variación en el período: {variation:.2f}%")
    else:
        print("No se pudieron obtener datos de Alpha Vantage")

if __name__ == "__main__":
    asyncio.run(main()) 