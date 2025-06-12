import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_alpha_vantage_integration():
    BASE_URL = "http://localhost:5000"
    
    def print_response(title, response):
        print(f"\n=== {title} ===")
        print(f"Status Code: {response.status_code}")
        try:
            print("Response:")
            print(json.dumps(response.json(), indent=2))
        except:
            print("Raw response:", response.text)
        print("="*50)

    # Test 1: Verificar que el servidor está funcionando
    print("\nIniciando pruebas de integración con Alpha Vantage...")
    
    try:
        # Test de conexión básica
        response = requests.get(f"{BASE_URL}/")
        print_response("Test de Conexión", response)

        # Test del endpoint de mercado (Alpha Vantage)
        print("\nProbando endpoint de mercado (Alpha Vantage)...")
        response = requests.post(f"{BASE_URL}/api/market")
        print_response("Datos de Mercado", response)

        # Test del endpoint de historial
        print("\nProbando endpoint de historial...")
        response = requests.get(f"{BASE_URL}/api/market/history")
        print_response("Historial de Precios", response)

        # Verificar la estructura de archivos
        data_path = "data/market"
        if os.path.exists(data_path):
            print("\nVerificando archivos guardados:")
            for root, dirs, files in os.walk(data_path):
                for file in files:
                    if file.endswith('.json'):
                        file_path = os.path.join(root, file)
                        print(f"\nContenido de {file_path}:")
                        with open(file_path, 'r') as f:
                            print(json.dumps(json.load(f), indent=2))
        else:
            print(f"\nDirectorio {data_path} no encontrado")

    except requests.exceptions.ConnectionError:
        print("ERROR: No se pudo conectar al servidor. Asegúrate de que esté corriendo en localhost:5000")
    except Exception as e:
        print(f"Error durante las pruebas: {str(e)}")

if __name__ == "__main__":
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        print("ERROR: ALPHA_VANTAGE_API_KEY no está configurada en el archivo .env")
        exit(1)
    
    print(f"API Key configurada: {api_key[:4]}...{api_key[-4:]}")
    test_alpha_vantage_integration() 