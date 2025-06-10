import requests
import json
import os
from datetime import datetime, timezone
from colorama import init, Fore, Style

# Inicializar colorama para colores en la consola
init()

def print_response(title, response, data=None):
    print(f"\n{Fore.CYAN}=== {title} ==={Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Status Code:{Style.RESET_ALL} {response.status_code}")
    print(f"{Fore.YELLOW}Response:{Style.RESET_ALL}")
    print(json.dumps(response.json(), indent=2))
    if data:
        print(f"{Fore.YELLOW}Sent Data:{Style.RESET_ALL}")
        print(json.dumps(data, indent=2))
    print(f"{Fore.CYAN}{'='*40}{Style.RESET_ALL}\n")

def test_api():
    BASE_URL = "http://localhost:5000/api"
    current_date = datetime.now(timezone.utc).isoformat()

    # Test 1: Verificar que el servidor está funcionando
    try:
        response = requests.get("http://localhost:5000/")
        print_response("Test Conexión al Servidor", response)
    except requests.exceptions.ConnectionError:
        print(f"{Fore.RED}ERROR: No se pudo conectar al servidor. Asegúrate de que esté corriendo en localhost:5000{Style.RESET_ALL}")
        return

    # Test 2: Obtener datos de mercado desde Alpha Vantage
    print(f"\n{Fore.CYAN}Probando integración con Alpha Vantage...{Style.RESET_ALL}")
    try:
        response = requests.post(f"{BASE_URL}/market")
        print_response("Test Alpha Vantage Market Data", response)

        # Obtener historial de precios
        response = requests.get(f"{BASE_URL}/market/history")
        print_response("Test Alpha Vantage Price History", response)
    except Exception as e:
        print(f"{Fore.RED}Error al obtener datos de Alpha Vantage: {str(e)}{Style.RESET_ALL}")

    # Test 3: Enviar datos de GeoPark
    geopark_data = {
        "date": current_date,
        "production": 10500.5,
        "revenue": 850000.0,
        "wells": 25,
        "location": "Colombia - Llanos",
        "status": "active"
    }
    response = requests.post(f"{BASE_URL}/geopark", json=geopark_data)
    print_response("Test POST GeoPark Data", response, geopark_data)

    # Test 4: Enviar datos de Brent
    brent_data = {
        "date": current_date,
        "price": 85.75,
        "volume": 250000,
        "change": 0.025
    }
    response = requests.post(f"{BASE_URL}/brent", json=brent_data)
    print_response("Test POST Brent Data", response, brent_data)

    # Test 5: Obtener reporte diario
    date_str = current_date.split('T')[0]
    response = requests.get(f"{BASE_URL}/daily-report/{date_str}")
    print_response("Test GET Daily Report", response)

    # Test 6: Verificar estructura de archivos
    print(f"{Fore.GREEN}Verificando archivos generados...{Style.RESET_ALL}")
    import os
    base_path = "data"
    date_parts = datetime.now().strftime("%Y/%m/%d").split('/')
    
    paths_to_check = [
        f"{base_path}/geopark/{'/'.join(date_parts)}/data.json",
        f"{base_path}/market/{'/'.join(date_parts)}/data.json",
        f"{base_path}/brent/{'/'.join(date_parts)}/data.json"
    ]

    for path in paths_to_check:
        if os.path.exists(path):
            print(f"{Fore.GREEN}✓ Archivo creado: {path}{Style.RESET_ALL}")
            with open(path, 'r') as f:
                print(f"{Fore.YELLOW}Contenido:{Style.RESET_ALL}")
                print(json.dumps(json.load(f), indent=2))
        else:
            print(f"{Fore.RED}✗ Archivo no encontrado: {path}{Style.RESET_ALL}")

if __name__ == "__main__":
    if not os.getenv('ALPHA_VANTAGE_API_KEY'):
        print(f"{Fore.RED}ERROR: ALPHA_VANTAGE_API_KEY no está configurada en las variables de entorno{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Por favor, configura la variable de entorno ALPHA_VANTAGE_API_KEY con tu API key de Alpha Vantage{Style.RESET_ALL}")
        exit(1)
    
    print(f"{Fore.CYAN}Iniciando pruebas de API...{Style.RESET_ALL}")
    test_api() 