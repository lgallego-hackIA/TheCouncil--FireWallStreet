"""
Script para probar la conexión a Vercel Blob Storage.
"""
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
import requests
from src.infrastructure.database.vercel_blob import blob_store

# Cargar variables de entorno
load_dotenv()

# Intentar importar el módulo de Vercel Blob Storage
try:
    from src.infrastructure.storage.blob_storage import BlobStorageAdapter
    print("✓ Módulo BlobStorageAdapter importado correctamente")
except ImportError as e:
    print(f"❌ Error importando BlobStorageAdapter: {str(e)}")
    sys.exit(1)

VERCEL_BLOB_API = "https://blob.vercel-storage.com/api/v1/"

def test_vercel_blob_connection():
    try:
        # Obtener el token de las variables de entorno
        token = os.getenv('BLOB_READ_WRITE_TOKEN')
        if not token:
            raise ValueError("BLOB_READ_WRITE_TOKEN no encontrado en las variables de entorno")

        # Intentar subir un blob de prueba
        print("\nIntentando subir un blob de prueba...")
        test_content = b"Este es un archivo de prueba para verificar la conexion"
        result = blob_store.put(
            path="test-connection.txt",
            data=test_content,
            options={
                "token": token,
                "addRandomSuffix": "true"
            },
            verbose=False  # Desactivar el modo verbose para evitar el error de progreso
        )
        print(f"Blob subido exitosamente: {result}")

        # Intentar eliminar el blob de prueba
        print("\nIntentando eliminar el blob de prueba...")
        if 'url' in result:
            delete_result = blob_store.delete(result['url'], options={"token": token})
            print(f"Blob eliminado exitosamente: {delete_result}")
        else:
            print("No se pudo obtener la URL del blob para eliminarlo")

        print("\n¡Conexión con Vercel Blob Storage verificada exitosamente!")
        return True

    except Exception as e:
        print(f"\nError al verificar la conexión: {str(e)}")
        return False

def test_blob_storage():
    """Prueba la funcionalidad de Vercel Blob Storage"""
    print("\n=== Prueba de conexión a Vercel Blob Storage ===")
    
    # Verificar si Blob Storage está disponible
    is_available = BlobStorageAdapter.is_available()
    print(f"¿Blob Storage disponible?: {is_available}")
    
    if not is_available:
        print("❌ Vercel Blob Storage no está disponible. Verificando el motivo:")
        from src.infrastructure.storage.blob_storage import VERCEL_BLOB_AVAILABLE, _CACHED_IMPORT_ERROR_DETAILS
        print(f"VERCEL_BLOB_AVAILABLE: {VERCEL_BLOB_AVAILABLE}")
        print(f"Error de importación: {_CACHED_IMPORT_ERROR_DETAILS}")
        return False
    
    # Crear una instancia del adaptador
    adapter = BlobStorageAdapter()
    
    # Crear datos de prueba
    test_data = {
        "test": True,
        "timestamp": datetime.now().isoformat(),
        "message": "Prueba de Vercel Blob Storage"
    }
    
    # Convertir a JSON
    test_json = json.dumps(test_data).encode('utf-8')
    
    try:
        # Guardar en Blob Storage
        print("\nGuardando datos en Blob Storage...")
        result = adapter.put_blob("test_blob.json", test_json)
        print(f"✓ Datos guardados. URL: {result.get('url')}")
        
        # Leer de Blob Storage
        print("\nLeyendo datos de Blob Storage...")
        blob_data = adapter.get_blob("test_blob.json")
        loaded_data = json.loads(blob_data.decode('utf-8'))
        print(f"✓ Datos leídos: {loaded_data}")
        
        # Listar blobs
        print("\nListando blobs en el almacenamiento...")
        blobs = adapter.list_blobs()
        print(f"✓ Blobs encontrados: {len(blobs)}")
        for blob in blobs[:5]:  # Mostrar solo los primeros 5
            print(f"  - {blob.get('pathname')}: {blob.get('url')}")
        
        # Eliminar el blob de prueba
        print("\nEliminando blob de prueba...")
        adapter.delete_blob("test_blob.json")
        print("✓ Blob eliminado correctamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {str(e)}")
        return False

if __name__ == "__main__":
    test_vercel_blob_connection() 