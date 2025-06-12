from datetime import datetime, timedelta
import random

# Datos de ejemplo para Geopark
def generate_geopark_data(start_date: datetime, days: int = 30):
    data = []
    current_date = start_date
    
    for _ in range(days):
        data.append({
            "date": current_date,
            "production": round(random.uniform(1000, 5000), 2),  # Producción entre 1000 y 5000 barriles
            "revenue": round(random.uniform(50000, 200000), 2),  # Ingresos entre 50,000 y 200,000
            "wells": random.randint(5, 20),  # Entre 5 y 20 pozos activos
            "location": random.choice(["Campo A", "Campo B", "Campo C"]),
            "status": random.choice(["Operativo", "Mantenimiento", "Optimización"])
        })
        current_date += timedelta(days=1)
    
    return data

# Datos de ejemplo para Market Cap
def generate_market_cap_data(start_date: datetime, days: int = 30):
    data = []
    current_date = start_date
    base_cap = 1000000000  # 1 billón de dólares como base
    
    for _ in range(days):
        # Variación diaria aleatoria entre -2% y +2%
        variation = random.uniform(-0.02, 0.02)
        base_cap *= (1 + variation)
        
        data.append({
            "date": current_date,
            "market_cap": round(base_cap, 2),
            "shares_outstanding": round(base_cap / random.uniform(7.5, 8.5), 0),  # Precio por acción entre 7.5 y 8.5
            "volume": round(random.uniform(100000, 500000), 0)  # Volumen entre 100,000 y 500,000
        })
        current_date += timedelta(days=1)
    
    return data

# Datos de ejemplo para Brent
def generate_brent_data(start_date: datetime, days: int = 30):
    data = []
    current_date = start_date
    base_price = 80.0  # Precio base de 80 USD por barril
    
    for _ in range(days):
        # Variación diaria aleatoria entre -1% y +1%
        variation = random.uniform(-0.01, 0.01)
        base_price *= (1 + variation)
        
        data.append({
            "date": current_date,
            "price": round(base_price, 2),
            "change": round(variation * 100, 2),  # Cambio porcentual
            "volume": round(random.uniform(50000, 200000), 0)  # Volumen entre 50,000 y 200,000
        })
        current_date += timedelta(days=1)
    
    return data

# Generar datos para el último mes
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

seed_data = {
    "geopark_data": generate_geopark_data(start_date),
    "market_cap_data": generate_market_cap_data(start_date),
    "brent_data": generate_brent_data(start_date)
} 