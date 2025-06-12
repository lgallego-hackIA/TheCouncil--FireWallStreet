import asyncio
import os
from dotenv import load_dotenv
from config.database import connect_and_check_db, get_database, close_db_connection

async def test_connection():
    # Cargar variables de entorno
    load_dotenv()
    
    # Verificar que tenemos la URL de MongoDB
    mongodb_url = os.getenv('MONGODB_URL')
    if not mongodb_url:
        print("Error: No se encontró la variable de entorno MONGODB_URL")
        return False
    
    # Probar la conexión
    connection_success = await connect_and_check_db()
    if connection_success:
        db = get_database()
        try:
            # Intentar una operación simple
            test_collection = db.test_collection
            result = await test_collection.insert_one({"test": "connection"})
            print(f"Documento de prueba insertado con ID: {result.inserted_id}")
            
            # Leer el documento insertado
            doc = await test_collection.find_one({"test": "connection"})
            print(f"Documento leído: {doc}")
            
            # Limpiar el documento de prueba
            await test_collection.delete_one({"test": "connection"})
            print("Documento de prueba eliminado")
            
        except Exception as e:
            print(f"Error durante las operaciones de prueba: {e}")
            return False
        finally:
            await close_db_connection()
    
    return connection_success

if __name__ == "__main__":
    print("Iniciando prueba de conexión a MongoDB...")
    asyncio.run(test_connection()) 