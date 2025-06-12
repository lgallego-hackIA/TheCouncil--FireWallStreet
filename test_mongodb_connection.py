import asyncio
import time
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi

async def test_mongodb_connection():
    print("=== Test de Conexión a MongoDB Atlas ===\n")
    
    # Paso 1: Configuración de la conexión
    print("Paso 1: Configurando conexión...")
    MONGODB_URL = "mongodb+srv://lgallego:LauGalle3101@clusteria.9fn928a.mongodb.net/?retryWrites=true&w=majority&appName=ClusterIA"
    
    try:
        # Paso 2: Crear cliente
        print("\nPaso 2: Creando cliente MongoDB...")
        client = AsyncIOMotorClient(MONGODB_URL, server_api=ServerApi('1'))
        print("✓ Cliente creado exitosamente")

        # Paso 3: Verificar conexión
        print("\nPaso 3: Verificando conexión...")
        start_time = time.time()
        await client.admin.command('ping')
        end_time = time.time()
        print(f"✓ Conexión exitosa (Tiempo de respuesta: {(end_time - start_time)*1000:.2f}ms)")

        # Paso 4: Listar bases de datos
        print("\nPaso 4: Listando bases de datos...")
        databases = await client.list_database_names()
        print("Bases de datos disponibles:")
        for db in databases:
            print(f"  - {db}")

        # Paso 5: Acceder a la base de datos específica
        print("\nPaso 5: Accediendo a la base de datos 'thecouncil'...")
        db = client.thecouncil
        collections = await db.list_collection_names()
        print("Colecciones en 'thecouncil':")
        for collection in collections:
            print(f"  - {collection}")
            # Contar documentos en la colección
            count = await db[collection].count_documents({})
            print(f"    Documentos: {count}")

        # Paso 6: Prueba de operaciones CRUD
        print("\nPaso 6: Probando operaciones CRUD...")
        test_collection = db.test_collection
        
        # Create
        print("• Insertando documento de prueba...")
        doc = {"test_id": "connection_test", "timestamp": time.time()}
        result = await test_collection.insert_one(doc)
        print(f"✓ Documento insertado con ID: {result.inserted_id}")
        
        # Read
        print("• Leyendo documento...")
        found_doc = await test_collection.find_one({"test_id": "connection_test"})
        print(f"✓ Documento leído: {found_doc}")
        
        # Update
        print("• Actualizando documento...")
        update_result = await test_collection.update_one(
            {"test_id": "connection_test"},
            {"$set": {"updated": True}}
        )
        print(f"✓ Documento actualizado: {update_result.modified_count} modificación(es)")
        
        # Delete
        print("• Eliminando documento de prueba...")
        delete_result = await test_collection.delete_one({"test_id": "connection_test"})
        print(f"✓ Documento eliminado: {delete_result.deleted_count} eliminación(es)")

        print("\n=== Resumen del Test ===")
        print("✓ Conexión establecida correctamente")
        print("✓ Operaciones CRUD realizadas con éxito")
        print("✓ Base de datos y colecciones accesibles")
        
    except Exception as e:
        print(f"\n❌ Error durante el test: {str(e)}")
    finally:
        # Paso 7: Cerrar conexión
        print("\nPaso 7: Cerrando conexión...")
        client.close()
        print("✓ Conexión cerrada")

if __name__ == "__main__":
    asyncio.run(test_mongodb_connection()) 