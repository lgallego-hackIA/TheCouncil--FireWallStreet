import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import json

async def verify_user_permissions():
    print("=== Verificación de Permisos de MongoDB Atlas ===\n")
    
    # URL de conexión con la nueva contraseña
    mongodb_url = "mongodb+srv://lgallego:jqsfcmZL5IgfeggS@clusteria.9fn928a.mongodb.net/?retryWrites=true&w=majority&appName=ClusterIA"
    
    try:
        # 1. Intentar conexión
        print("1. Probando conexión básica...")
        client = AsyncIOMotorClient(mongodb_url, server_api=ServerApi('1'))
        await client.admin.command('ping')
        print("✓ Conexión básica exitosa")
        
        # 2. Verificar roles y permisos
        print("\n2. Verificando roles del usuario...")
        user_info = await client.admin.command('usersInfo', 'lgallego')
        print("\nInformación del usuario:")
        print(json.dumps(user_info, indent=2))
        
        # 3. Probar operaciones CRUD
        print("\n3. Probando operaciones CRUD...")
        db = client.thecouncil
        test_collection = db.permission_test
        
        try:
            # Create
            print("• Intentando crear documento...")
            result = await test_collection.insert_one({
                "test": "permission_verification",
                "status": "testing"
            })
            print(f"✓ Documento creado con ID: {result.inserted_id}")
            
            # Read
            print("\n• Intentando leer documento...")
            doc = await test_collection.find_one({"test": "permission_verification"})
            print(f"✓ Documento leído: {doc}")
            
            # Update
            print("\n• Intentando actualizar documento...")
            update_result = await test_collection.update_one(
                {"test": "permission_verification"},
                {"$set": {"status": "verified"}}
            )
            print(f"✓ Documento actualizado: {update_result.modified_count} modificación(es)")
            
            # Delete
            print("\n• Intentando eliminar documento...")
            delete_result = await test_collection.delete_one({"test": "permission_verification"})
            print(f"✓ Documento eliminado: {delete_result.deleted_count} eliminación(es)")
            
            print("\n✓ Todas las operaciones CRUD completadas exitosamente")
            print("✓ El usuario tiene los permisos necesarios (readWrite)")
            
        except Exception as e:
            print(f"\n❌ Error durante las operaciones CRUD: {str(e)}")
            print("❌ El usuario puede no tener los permisos necesarios")
        
        # 4. Verificar bases de datos disponibles
        print("\n4. Verificando bases de datos accesibles...")
        databases = await client.list_database_names()
        print("Bases de datos disponibles:")
        for db_name in databases:
            print(f"  - {db_name}")
            db = client[db_name]
            try:
                collections = await db.list_collection_names()
                print(f"    Colecciones:")
                for collection in collections:
                    print(f"      • {collection}")
            except Exception as e:
                print(f"    ❌ No se pueden listar colecciones: {str(e)}")
        
    except Exception as e:
        print(f"\n❌ Error de conexión: {str(e)}")
        if "bad auth" in str(e):
            print("\nPosibles soluciones:")
            print("1. Verifica que la contraseña sea correcta")
            print("2. Asegúrate de que el usuario tenga los permisos necesarios")
            print("3. Verifica que la IP esté en la lista blanca de MongoDB Atlas")
    finally:
        if 'client' in locals():
            client.close()
            print("\nConexión cerrada")

if __name__ == "__main__":
    asyncio.run(verify_user_permissions()) 