import requests
from datetime import datetime, timezone

def test_endpoints():
    # URL base (ajusta según tu configuración)
    BASE_URL = "http://localhost:5000/api"
    
    # Fecha actual
    current_date = datetime.now(timezone.utc).isoformat()

    # Test GeoPark endpoint
    geopark_data = {
        "date": current_date,
        "production": 10500.5,  # barriles por día
        "revenue": 850000.0,    # USD
        "wells": 25,            # pozos activos
        "location": "Colombia - Llanos",
        "status": "active"
    }
    
    print("\nEnviando datos de GeoPark...")
    response = requests.post(f"{BASE_URL}/geopark", json=geopark_data)
    print(f"Respuesta: {response.status_code}")
    print(response.json())

    # Test Market Cap endpoint
    market_data = {
        "date": current_date,
        "stock_price": 12.45,    # USD
        "market_cap": 750000000, # USD
        "volume": 125000,        # acciones
        "currency": "USD"
    }
    
    print("\nEnviando datos de Market Cap...")
    response = requests.post(f"{BASE_URL}/market", json=market_data)
    print(f"Respuesta: {response.status_code}")
    print(response.json())

    # Test Brent endpoint
    brent_data = {
        "date": current_date,
        "price": 85.75,     # USD por barril
        "volume": 250000,   # contratos
        "change": 0.025     # cambio porcentual
    }
    
    print("\nEnviando datos del Brent...")
    response = requests.post(f"{BASE_URL}/brent", json=brent_data)
    print(f"Respuesta: {response.status_code}")
    print(response.json())

    # Test Daily Report endpoint
    print("\nConsultando reporte diario...")
    response = requests.get(f"{BASE_URL}/daily-report/{current_date}")
    print(f"Respuesta: {response.status_code}")
    print(response.json())

if __name__ == "__main__":
    test_endpoints() 