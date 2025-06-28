# PER Tests - Aplicación de Exámenes Aleatorios

## Descripción
Proyecto de aplicación para generar exámenes aleatorios de PER España. La aplicación consta de:
- **API Backend**: FastAPI que genera exámenes dinámicos y los corrige
- **Cliente Web**: Interfaz simple para realizar exámenes
- **Fuente de Datos**: Archivos YAML organizados por categorías

## Arquitectura

### Tecnologías Utilizadas
- **FastAPI**: Framework web moderno y rápido para APIs
- **Pydantic**: Validación de datos y serialización
- **PyYAML**: Procesamiento de archivos YAML
- **Uvicorn**: Servidor ASGI para ejecutar FastAPI

### Estructura del Proyecto
```
per-tests/
├── app/                      # Código de la aplicación
│   ├── main.py              # Punto de entrada de FastAPI
│   ├── models/              # Modelos Pydantic
│   ├── services/            # Lógica de negocio
│   ├── routers/             # Endpoints de la API
│   └── core/                # Configuración y utilidades
├── data/                    # Archivos YAML con preguntas
├── static/                  # Frontend (HTML, CSS, JS)
├── requirements.txt         # Dependencias Python
└── README.md
```

## Instalación y Ejecución

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Ejecutar la aplicación:
```bash
uvicorn app.main:app --reload
```

3. Acceder a:
- API: http://localhost:8000
- Documentación: http://localhost:8000/docs
- Cliente Web: http://localhost:8000/static/index.html

## Despliegue en Azure Web Apps
La aplicación está configurada para desplegarse directamente en Azure Web Apps usando el archivo `requirements.txt` y la estructura estándar de FastAPI.