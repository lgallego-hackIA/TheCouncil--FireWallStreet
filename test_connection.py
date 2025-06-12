import asyncio
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi

async def test_mongodb_connection():
    # URL de MongoDB con la nueva contraseña
    mongodb_url = "mongodb+srv://lgallego:jqsfcmZL5IgfeggS@clusteria.9fn928a.mongodb.net/?retryWrites=true&w=majority&appName=ClusterIA"
    
    try:
        # Crear cliente de MongoDB
        client = AsyncIOMotorClient(mongodb_url, server_api=ServerApi('1'))
        
        # Verificar la conexión
        await client.admin.command('ping')
        print("¡Conexión exitosa a MongoDB Atlas!")
        
        # Obtener lista de bases de datos
        database_names = await client.list_database_names()
        print("\nBases de datos disponibles:")
        for db_name in database_names:
            print(f"- {db_name}")
        
        # Probar operaciones en la base de datos thecouncil
        db = client.thecouncil
        
        # Listar colecciones
        collections = await db.list_collection_names()
        print("\nColecciones en 'thecouncil':")
        for collection in collections:
            print(f"- {collection}")
        
        # Insertar un documento de prueba
        test_collection = db.test_collection
        result = await test_collection.insert_one({"test": "connection_test"})
        print(f"\nDocumento de prueba insertado con ID: {result.inserted_id}")
        
        # Leer el documento insertado
        doc = await test_collection.find_one({"test": "connection_test"})
        print(f"Documento leído: {doc}")
        
        # Eliminar el documento de prueba
        await test_collection.delete_one({"test": "connection_test"})
        print("Documento de prueba eliminado")
        
    except Exception as e:
        print(f"Error de conexión: {str(e)}")
    finally:
        # Cerrar la conexión
        if 'client' in locals():
            client.close()
            print("\nConexión cerrada")

if __name__ == "__main__":
    print("=== Test de Conexión a MongoDB Atlas ===\n")
    asyncio.run(test_mongodb_connection()) 