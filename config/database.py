import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi

# MongoDB connection string
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb+srv://lgallego:LauGalle3101@clusteria.9fn928a.mongodb.net/?retryWrites=true&w=majority&appName=ClusterIA')

# Create a new client and connect to the server
client = AsyncIOMotorClient(MONGODB_URL, server_api=ServerApi('1'))
db = client.get_database("thecouncil")  # Nombre de tu base de datos

# Función para verificar la conexión
async def connect_and_check_db():
    try:
        # Send a ping to confirm a successful connection
        await client.admin.command('ping')
        print("¡Conexión exitosa a MongoDB!")
        return True
    except Exception as e:
        print(f"Error conectando a MongoDB: {e}")
        return False

# Función para cerrar la conexión
async def close_db_connection():
    try:
        client.close()
        print("Conexión a MongoDB cerrada")
    except Exception as e:
        print(f"Error cerrando la conexión: {e}")

# Función para obtener la conexión a la base de datos
def get_database():
    return db 