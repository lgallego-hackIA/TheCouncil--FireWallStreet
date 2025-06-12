import asyncio
import sys
import os
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Agregar el directorio raíz al path para poder importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar los datos de ejemplo
from data.seed_data import seed_data

# Cargar variables de entorno
load_dotenv()

async def populate_database():
    try:
        # Obtener la URL de conexión de MongoDB desde las variables de entorno
        mongo_url = os.getenv('MONGODB_URL')
        if not mongo_url:
            raise ValueError("MONGODB_URL no encontrada en las variables de entorno")

        # Conectar a MongoDB
        client = MongoClient(mongo_url)
        db = client['thecouncil']
        
        # Colecciones
        geopark_collection = db['geopark_data']
        market_cap_collection = db['market_cap_data']
        brent_collection = db['brent_data']

        # Limpiar colecciones existentes
        print("Limpiando colecciones existentes...")
        geopark_collection.delete_many({})
        market_cap_collection.delete_many({})
        brent_collection.delete_many({})

        # Insertar datos de ejemplo
        print("Insertando datos de Geopark...")
        geopark_collection.insert_many(seed_data['geopark_data'])
        
        print("Insertando datos de Market Cap...")
        market_cap_collection.insert_many(seed_data['market_cap_data'])
        
        print("Insertando datos de Brent...")
        brent_collection.insert_many(seed_data['brent_data'])

        # Verificar la inserción
        print("\nVerificando datos insertados:")
        print(f"Registros de Geopark: {geopark_collection.count_documents({})}")
        print(f"Registros de Market Cap: {market_cap_collection.count_documents({})}")
        print(f"Registros de Brent: {brent_collection.count_documents({})}")

        print("\n¡Base de datos poblada exitosamente!")
        
    except Exception as e:
        print(f"Error al poblar la base de datos: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(populate_database()) 