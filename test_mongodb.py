import os
import sys
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Cargar variables de entorno
load_dotenv()

def test_mongodb_connection():
    """Prueba la conexión a MongoDB Atlas con diagnóstico detallado"""
    try:
        print("\n=== Probando conexión a MongoDB Atlas ===")
        
        # Obtener la URL de conexión
        mongo_url = os.getenv('MONGODB_URL')
        if not mongo_url:
            raise ValueError("MONGODB_URL no encontrada en las variables de entorno")
        
        print(f"URL de conexión (oculta): mongodb+srv://****:****@clusteria.9fn928a.mongodb.net/")
        
        # Configurar el cliente con timeout más corto para diagnóstico rápido
        client = MongoClient(
            mongo_url,
            serverSelectionTimeoutMS=5000,  # 5 segundos de timeout
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        
        # Intentar obtener información del servidor
        print("\nIntentando conectar al servidor...")
        server_info = client.server_info()
        print(f"✓ Conexión exitosa a MongoDB Atlas")
        print(f"  - Versión del servidor: {server_info['version']}")
        
        # Verificar la base de datos
        db = client['thecouncil']
        print(f"  - Base de datos: thecouncil")
        
        # Listar colecciones
        collections = db.list_collection_names()
        print(f"\nColecciones encontradas ({len(collections)}):")
        for collection in collections:
            count = db[collection].count_documents({})
            print(f"  * {collection}: {count} documentos")
        
        # Verificar permisos intentando una operación de escritura
        print("\nVerificando permisos de escritura...")
        test_collection = db['connection_test']
        test_doc = {"test": "connection", "timestamp": "test"}
        result = test_collection.insert_one(test_doc)
        print(f"✓ Permisos de escritura verificados (ID: {result.inserted_id})")
        
        # Limpiar el documento de prueba
        test_collection.delete_one({"_id": result.inserted_id})
        print("✓ Documento de prueba eliminado")
        
        return True

    except ServerSelectionTimeoutError as e:
        print(f"\n✗ Error de timeout al conectar al servidor:")
        print(f"  - El servidor no respondió en el tiempo esperado")
        print(f"  - Verifica que la IP desde donde te conectas esté en la lista blanca de MongoDB Atlas")
        print(f"  - Error detallado: {str(e)}")
        return False
        
    except ConnectionFailure as e:
        print(f"\n✗ Error de conexión:")
        print(f"  - No se pudo establecer conexión con el servidor")
        print(f"  - Verifica que la URL de conexión sea correcta")
        print(f"  - Error detallado: {str(e)}")
        return False
        
    except Exception as e:
        print(f"\n✗ Error inesperado:")
        print(f"  - Tipo de error: {type(e).__name__}")
        print(f"  - Mensaje: {str(e)}")
        return False
        
    finally:
        if 'client' in locals():
            client.close()
            print("\nConexión cerrada")

if __name__ == "__main__":
    success = test_mongodb_connection()
    sys.exit(0 if success else 1) 