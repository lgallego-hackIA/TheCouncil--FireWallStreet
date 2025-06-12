import os
import sys
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from src.infrastructure.database.vercel_blob import blob_store

# Cargar variables de entorno
load_dotenv()

def test_mongodb_connection():
    """Prueba la conexión a MongoDB Atlas"""
    try:
        print("\n=== Probando conexión a MongoDB Atlas ===")
        mongo_url = os.getenv('MONGODB_URL')
        if not mongo_url:
            raise ValueError("MONGODB_URL no encontrada en las variables de entorno")

        # Conectar a MongoDB
        client = MongoClient(mongo_url)
        
        # Verificar la conexión
        db = client['thecouncil']
        server_info = client.server_info()
        
        print(f"✓ Conexión exitosa a MongoDB Atlas")
        print(f"  - Versión del servidor: {server_info['version']}")
        print(f"  - Base de datos: thecouncil")
        
        # Listar colecciones
        collections = db.list_collection_names()
        print(f"  - Colecciones encontradas: {len(collections)}")
        for collection in collections:
            count = db[collection].count_documents({})
            print(f"    * {collection}: {count} documentos")
        
        return True

    except Exception as e:
        print(f"✗ Error al conectar a MongoDB Atlas: {str(e)}")
        return False
    finally:
        if 'client' in locals():
            client.close()

def test_vercel_blob_connection():
    """Prueba la conexión a Vercel Blob Storage"""
    try:
        print("\n=== Probando conexión a Vercel Blob Storage ===")
        token = os.getenv('BLOB_READ_WRITE_TOKEN')
        if not token:
            raise ValueError("BLOB_READ_WRITE_TOKEN no encontrado en las variables de entorno")

        # Intentar subir un blob de prueba
        print("Intentando subir un blob de prueba...")
        test_content = b"Este es un archivo de prueba para verificar la conexion"
        result = blob_store.put(
            path="test-connection.txt",
            data=test_content,
            options={
                "token": token,
                "addRandomSuffix": "true"
            },
            verbose=False
        )
        print(f"✓ Blob subido exitosamente: {result}")

        # Intentar eliminar el blob de prueba
        print("\nIntentando eliminar el blob de prueba...")
        if 'url' in result:
            delete_result = blob_store.delete(result['url'], options={"token": token})
            print(f"✓ Blob eliminado exitosamente: {delete_result}")
        else:
            print("✗ No se pudo obtener la URL del blob para eliminarlo")

        print("\n✓ Conexión con Vercel Blob Storage verificada exitosamente!")
        return True

    except Exception as e:
        print(f"✗ Error al verificar la conexión con Vercel Blob Storage: {str(e)}")
        return False

def main():
    """Función principal que ejecuta todas las pruebas de conexión"""
    print("Iniciando pruebas de conexión...")
    
    # Probar conexión a MongoDB
    mongodb_success = test_mongodb_connection()
    
    # Probar conexión a Vercel Blob
    vercel_blob_success = test_vercel_blob_connection()
    
    # Resumen final
    print("\n=== Resumen de pruebas ===")
    print(f"MongoDB Atlas: {'✓ Conectado' if mongodb_success else '✗ Error de conexión'}")
    print(f"Vercel Blob: {'✓ Conectado' if vercel_blob_success else '✗ Error de conexión'}")
    
    # Retornar éxito solo si ambas conexiones funcionan
    return mongodb_success and vercel_blob_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 