import asyncio
from config.database import connect_and_check_db, get_database, close_db_connection

async def query_council_data():
    connection_success = await connect_and_check_db()
    if connection_success:
        try:
            db = get_database()
            council_collection = db.council_data
            
            # Obtener el documento
            data = await council_collection.find_one({"id": "1000"})
            
            if data:
                print("\n=== Detalles del Consejo ===")
                print("\nConstantes:")
                for key, value in data['constants'].items():
                    print(f"{key}: ${value:,.2f}" if isinstance(value, (int, float)) else f"{key}: {value}")
                
                print("\n=== Detalles de Proveedores ===")
                for provider in data['providers']:
                    print(f"\nProveedor {provider['record_no']}:")
                    print(f"ID: {provider['provider_id']}")
                    print(f"Método de pago: {provider['payment_method']}")
                    print(f"NED: {provider['NED']}")
                    print(f"Chair of BoD: {provider['chair_of_bod']}")
                    print("Comités:")
                    for committee in provider['committees']:
                        roles = []
                        if committee['roles']['chair']:
                            roles.append("Chair")
                        if committee['roles']['member']:
                            roles.append("Member")
                        print(f"  - {committee['name']}: {', '.join(roles)}")
                
                # Análisis adicional
                print("\n=== Análisis de Datos ===")
                payment_methods = {}
                committee_chairs = 0
                committee_members = 0
                
                for provider in data['providers']:
                    # Contar métodos de pago
                    payment_methods[provider['payment_method']] = payment_methods.get(provider['payment_method'], 0) + 1
                    
                    # Contar roles en comités
                    for committee in provider['committees']:
                        if committee['roles']['chair']:
                            committee_chairs += 1
                        if committee['roles']['member']:
                            committee_members += 1
                
                print("\nDistribución de Métodos de Pago:")
                for method, count in payment_methods.items():
                    print(f"{method}: {count} proveedores")
                
                print(f"\nTotal de posiciones como Chair: {committee_chairs}")
                print(f"Total de posiciones como Member: {committee_members}")
                
            else:
                print("No se encontraron datos del consejo")
                
        except Exception as e:
            print(f"Error al consultar datos: {e}")
        finally:
            await close_db_connection()
    else:
        print("No se pudo establecer conexión con la base de datos")

if __name__ == "__main__":
    print("Consultando datos del consejo de MongoDB Atlas...")
    asyncio.run(query_council_data()) 