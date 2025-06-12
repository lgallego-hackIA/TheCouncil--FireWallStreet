import requests
from datetime import datetime, timedelta
import time
import statistics

def get_stock_price(symbol="GPRK"):
    """
    Obtiene el precio actual de la acción desde la API
    """
    url = f"https://geopark-financial-api.onrender.com/api/geopark/stock-price"
    params = {"symbol": symbol}
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return float(data["price"])
        else:
            print(f"Error al obtener el precio: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error en la solicitud: {str(e)}")
        return None

def calculate_average_price(samples=5, delay=2):
    """
    Calcula el promedio del precio de la acción tomando varias muestras
    
    Args:
        samples (int): Número de muestras a tomar
        delay (int): Tiempo de espera entre muestras en segundos
    """
    prices = []
    
    print(f"Obteniendo {samples} muestras de precios...")
    
    for i in range(samples):
        price = get_stock_price()
        if price is not None:
            prices.append(price)
            print(f"Muestra {i+1}: USD {price:.2f}")
        time.sleep(delay)  # Esperar entre llamadas para no sobrecargar la API
    
    if prices:
        average = statistics.mean(prices)
        print("\nResultados:")
        print(f"Número de muestras válidas: {len(prices)}")
        print(f"Precio promedio: USD {average:.2f}")
        print(f"Precio más alto: USD {max(prices):.2f}")
        print(f"Precio más bajo: USD {min(prices):.2f}")
        return average
    else:
        print("No se pudieron obtener precios válidos")
        return None

if __name__ == "__main__":
    print("Calculando el promedio del precio de las acciones de GeoPark (GPRK)")
    calculate_average_price() 