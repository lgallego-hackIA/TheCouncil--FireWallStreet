import asyncio
from datetime import datetime, timedelta
from models.action_history import ActionRecord
from services.action_history_service import ActionHistoryService

async def test_action_history():
    print("=== Test del Sistema de Historial de Acciones ===\n")
    
    # Inicializar el servicio
    service = ActionHistoryService()
    
    # 1. Registrar algunas acciones de ejemplo
    print("1. Registrando acciones de ejemplo...")
    
    # Acción de actualización de comité
    action1 = ActionRecord(
        action_type="committee_update",
        description="Actualización de miembros del comité C1",
        user="lgallego",
        details={
            "committee": "C1",
            "changes": "Agregado nuevo miembro",
            "affected_providers": ["1", "2"]
        }
    )
    
    # Acción de cambio de método de pago
    action2 = ActionRecord(
        action_type="payment_method_change",
        description="Cambio de método de pago de proveedor",
        user="lgallego",
        details={
            "old_method": "Cash & Shares",
            "new_method": "Full Shares"
        },
        related_provider_id="3"
    )
    
    # Acción de revisión de documentos
    action3 = ActionRecord(
        action_type="document_review",
        description="Revisión anual de documentación",
        user="admin",
        details={
            "document_type": "Annual Review",
            "status": "approved"
        }
    )
    
    # Registrar las acciones
    await service.record_action(action1)
    await service.record_action(action2)
    await service.record_action(action3)
    print("✓ Acciones registradas exitosamente")
    
    # 2. Obtener acciones del día
    print("\n2. Obteniendo acciones del día actual...")
    today_actions = await service.get_today_actions()
    print(f"Acciones registradas hoy: {len(today_actions)}")
    for action in today_actions:
        print(f"- {action.timestamp}: {action.description} (por {action.user})")
    
    # 3. Obtener acciones por usuario
    print("\n3. Obteniendo acciones del usuario 'lgallego'...")
    user_actions = await service.get_actions_by_date_range(
        start_date=datetime.now() - timedelta(days=7),
        user="lgallego"
    )
    print(f"Acciones de lgallego en los últimos 7 días: {len(user_actions)}")
    for action in user_actions:
        print(f"- {action.action_type}: {action.description}")
    
    # 4. Obtener acciones por proveedor
    print("\n4. Obteniendo acciones relacionadas con el proveedor 3...")
    provider_actions = await service.get_actions_by_provider("3")
    print(f"Acciones relacionadas con el proveedor 3: {len(provider_actions)}")
    for action in provider_actions:
        print(f"- {action.timestamp}: {action.description}")
    
    # 5. Obtener resumen de acciones
    print("\n5. Generando resumen de acciones...")
    summary = await service.get_action_summary(days=30)
    print(f"Resumen del periodo: {summary['period']}")
    print(f"Total de registros: {summary['total_records']}")
    print("\nAcciones por fecha y tipo:")
    for action in summary['actions_by_date']:
        print(f"- {action['_id']['date']} - {action['_id']['action_type']}: {action['count']} acciones")
        print(f"  Usuarios involucrados: {', '.join(action['users'])}")

if __name__ == "__main__":
    print("Iniciando prueba del sistema de historial...")
    asyncio.run(test_action_history()) 