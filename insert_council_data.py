import asyncio
from config.database import connect_and_check_db, get_database, close_db_connection

council_data = {
    "id": "1000",
    "constants": {
        "NED": 20000,
        "Chair_of_Committee": 5000,
        "Committee_Member": 2500,
        "Chair_of_BoD": 12500,
        "Fee_to_be_paid_in_shares": 25000,
        "share_price": 7.80
    },
    "providers": [
        {
            "provider_id": "1",
            "record_no": "No. 1",
            "payment_method": "Cash & Shares",
            "NED": True,
            "chair_of_bod": False,
            "committees": [
                {"name": "C1", "roles": {"chair": False, "member": True}},
                {"name": "C2", "roles": {"chair": True, "member": False}},
                {"name": "C4", "roles": {"chair": False, "member": True}}
            ]
        },
        {
            "provider_id": "2",
            "record_no": "No. 2",
            "payment_method": "Full Shares",
            "NED": True,
            "chair_of_bod": False,
            "committees": [
                {"name": "C1", "roles": {"chair": True, "member": False}},
                {"name": "C2", "roles": {"chair": False, "member": True}},
                {"name": "C3", "roles": {"chair": False, "member": True}}
            ]
        },
        {
            "provider_id": "3",
            "record_no": "No. 3",
            "payment_method": "Full Shares",
            "NED": True,
            "chair_of_bod": True,
            "committees": [
                {"name": "C1", "roles": {"chair": False, "member": True}},
                {"name": "C3", "roles": {"chair": False, "member": True}},
                {"name": "C5", "roles": {"chair": False, "member": True}}
            ]
        },
        {
            "provider_id": "4",
            "record_no": "No. 4",
            "payment_method": "Full Shares",
            "NED": True,
            "chair_of_bod": False,
            "committees": [
                {"name": "C1", "roles": {"chair": False, "member": True}},
                {"name": "C2", "roles": {"chair": False, "member": True}},
                {"name": "C3", "roles": {"chair": True, "member": False}},
                {"name": "C4", "roles": {"chair": False, "member": True}}
            ]
        },
        {
            "provider_id": "5",
            "record_no": "No. 5",
            "payment_method": "Cash & Shares",
            "NED": True,
            "chair_of_bod": False,
            "committees": [
                {"name": "C2", "roles": {"chair": False, "member": True}},
                {"name": "C4", "roles": {"chair": False, "member": True}},
                {"name": "C6", "roles": {"chair": True, "member": False}}
            ]
        },
        {
            "provider_id": "6",
            "record_no": "No. 6",
            "payment_method": "Cash & Shares",
            "NED": True,
            "chair_of_bod": False,
            "committees": [
                {"name": "C4", "roles": {"chair": False, "member": True}},
                {"name": "C6", "roles": {"chair": False, "member": True}}
            ]
        },
        {
            "provider_id": "7",
            "record_no": "No. 7",
            "payment_method": "Cash & Shares",
            "NED": True,
            "chair_of_bod": False,
            "committees": [
                {"name": "C5", "roles": {"chair": True, "member": False}}
            ]
        }
    ]
}

async def insert_council_data():
    # Conectar a la base de datos
    connection_success = await connect_and_check_db()
    if connection_success:
        try:
            db = get_database()
            
            # Crear colección para los datos del consejo
            council_collection = db.council_data
            
            # Insertar los datos
            result = await council_collection.insert_one(council_data)
            print(f"Datos insertados con ID: {result.inserted_id}")
            
            # Verificar la inserción
            inserted_data = await council_collection.find_one({"id": "1000"})
            if inserted_data:
                print("\nDatos insertados correctamente:")
                print(f"ID del documento: {inserted_data['id']}")
                print(f"Número de proveedores: {len(inserted_data['providers'])}")
                print("\nConstantes configuradas:")
                for key, value in inserted_data['constants'].items():
                    print(f"{key}: {value}")
                
                print("\nProveedores registrados:")
                for provider in inserted_data['providers']:
                    print(f"\nProveedor {provider['record_no']}:")
                    print(f"Método de pago: {provider['payment_method']}")
                    print(f"Número de comités: {len(provider['committees'])}")
            
        except Exception as e:
            print(f"Error al insertar datos: {e}")
        finally:
            await close_db_connection()
    else:
        print("No se pudo establecer conexión con la base de datos")

if __name__ == "__main__":
    print("Insertando datos del consejo en MongoDB Atlas...")
    asyncio.run(insert_council_data()) 