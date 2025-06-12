import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi

async def test_mongodb_connection():
    """Prueba la conexión a MongoDB Atlas"""
    print("\n=== Probando conexión a MongoDB Atlas ===")
    
    mongodb_url = "mongodb+srv://lgallego:jqsfcmZL5IgfeggS@clusteria.9fn928a.mongodb.net/?retryWrites=true&w=majority&appName=ClusterIA"
    
    try:
        # Crear cliente de MongoDB
        client = AsyncIOMotorClient(mongodb_url, server_api=ServerApi('1'))
        
        # Verificar la conexión
        await client.admin.command('ping')
        print("✓ Conexión exitosa a MongoDB Atlas")
        
        # Obtener lista de bases de datos
        database_names = await client.list_database_names()
        print("\nBases de datos disponibles:")
        for db_name in database_names:
            print(f"- {db_name}")
        
        # Probar operaciones en la base de datos thecouncil
        db = client.thecouncil
        collection = db.financial_data_collector_collection
        
        # Insertar un documento de prueba
        test_doc = {
            "test": True,
            "timestamp": datetime.now().isoformat()
        }
        result = await collection.insert_one(test_doc)
        print(f"\n✓ Documento de prueba insertado con ID: {result.inserted_id}")
        
        # Leer el documento insertado
        doc = await collection.find_one({"test": True})
        print(f"✓ Documento leído: {doc}")
        
        # Eliminar el documento de prueba
        await collection.delete_one({"test": True})
        print("✓ Documento de prueba eliminado")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error de conexión a MongoDB: {str(e)}")
        return False
    finally:
        if 'client' in locals():
            client.close()
            print("\nConexión cerrada")

async def test_prepopulate_endpoint():
    """Prueba el nuevo endpoint de prepoblación de datos"""
    print("\n=== Probando endpoint de prepoblación de datos ===")
    
    # Configurar fechas para la prueba
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    # Datos para la solicitud
    test_data = {
        "symbol": "GPRK",
        "start_date": start_date,
        "end_date": end_date
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/financial-data-collector/prepopulate",
                json=test_data
            ) as response:
                result = await response.json()
                
                if response.status == 200:
                    print("\n✓ Solicitud exitosa")
                    print("\nRespuesta:")
                    print(json.dumps(result, indent=2))
                    return True
                else:
                    print(f"\n❌ Error en la solicitud: {response.status}")
                    print("\nRespuesta de error:")
                    print(json.dumps(result, indent=2))
                    return False
                
    except Exception as e:
        print(f"\n❌ Error al probar el endpoint: {str(e)}")
        return False

async def main():
    """Función principal que ejecuta todas las pruebas"""
    print("=== Iniciando pruebas del Financial Data Collector ===")
    
    # Probar conexión a MongoDB
    mongodb_ok = await test_mongodb_connection()
    
    if mongodb_ok:
        # Probar el endpoint solo si la conexión a MongoDB fue exitosa
        await test_prepopulate_endpoint()
    else:
        print("\n❌ No se puede probar el endpoint debido a errores de conexión con MongoDB")

if __name__ == "__main__":
    asyncio.run(main()) 