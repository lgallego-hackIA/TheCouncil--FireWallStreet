# TheCouncil--FireWallStreet

## GeoPark Automation System

Sistema de automatización para la recopilación y análisis de datos de GeoPark, incluyendo:
- Datos de producción y operaciones
- Datos de mercado y capitalización
- Precios del Brent
- Generación automática de reportes

### Estructura del Proyecto

```
theCouncil/
├── frontend/                 # SPA React
│   ├── src/
│   │   ├── components/      # Componentes React
│   │   ├── pages/          # Páginas
│   │   ├── services/       # Servicios API
│   │   └── utils/          # Utilidades
│   └── package.json        # Dependencias frontend
├── src/                    # Backend Python
│   ├── api/               # Endpoints FastAPI
│   ├── data_models.py     # Modelos de datos
│   └── data_storage.py    # Almacenamiento
├── data/                  # Datos y recursos
└── requirements.txt       # Dependencias Python
```

### Características

- Frontend moderno con React y TypeScript
- Backend robusto con Python y FastAPI
- Almacenamiento estructurado de datos
- Automatización de recopilación de datos
- Dashboard interactivo
- Generación de reportes

### Instalación

1. Backend:
```bash
pip install -e .
```

2. Frontend:
```bash
cd frontend
npm install
```

### Ejecución

1. Backend:
```bash
python run.py
```

2. Frontend:
```bash
cd frontend
npm run dev
```

El servidor estará disponible en http://localhost:5000 y el frontend en http://localhost:3000
