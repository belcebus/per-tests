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
│   └── routers/             # Endpoints de la API
├── config/                  # Configuración centralizada
│   ├── __init__.py          # Paquete de configuración
│   └── settings.py          # Configuración principal
├── data/                    # Archivos YAML con preguntas
│   ├── exams/               # Archivos YAML de exámenes
│   ├── raw/                 # PDFs originales
│   │   ├── questions/       # PDFs de preguntas
│   │   └── answers/         # PDFs de respuestas
│   └── backups/             # Backups de archivos YAML
├── static/                  # Frontend (HTML, CSS, JS)
├── tools/                   # Scripts de extracción y procesamiento
│   ├── extraction/          # Scripts de extracción de datos
│   │   ├── madrid_extract_questions.py   # Extractor de preguntas de PDFs
│   │   ├── madrid_extract_answers.py     # Extractor OCR de respuestas
│   │   └── README.md        # Documentación de extracción
│   ├── processing/          # Scripts de procesamiento de datos
│   │   ├── madrid_merge_exam.py         # Aplicador de respuestas
│   │   └── README.md        # Documentación de procesamiento
│   ├── utils/               # Utilidades y análisis
│   │   ├── pdf_analyzer.py  # Analizador de PDFs
│   │   └── README.md        # Documentación de utilidades
│   └── README.md            # Documentación general de herramientas
├── .env.example             # Plantilla de variables de entorno
├── requirements.txt         # Dependencias completas
└── requirements-minimal.txt # Dependencias mínimas```
│   └── README.md                 # Documentación de herramientas
├── extracted_answers/       # Respuestas extraídas por OCR
├── pdfs/                   # Archivos PDF de exámenes oficiales
├── requirements.txt        # Dependencias Python
└── README.md
```

## Instalación y Ejecución

### Opción 1: Instalación Completa (Recomendada)
Incluye todas las dependencias para la aplicación web y las herramientas de procesamiento:

```bash
pip install -r requirements.txt
```

### Opción 2: Instalación Mínima (Solo Aplicación Web)
Solo las dependencias necesarias para ejecutar el servidor web:

```bash
pip install -r requirements-minimal.txt
```

### Ejecutar la Aplicación

```bash
uvicorn app.main:app --reload
```

### Accesos Disponibles
- API: http://localhost:8000
- Documentación: http://localhost:8000/docs
- Cliente Web: http://localhost:8000/static/index.html

## Dependencias del Proyecto

### Core (Aplicación Web)
- **FastAPI**: Framework web moderno para APIs REST
- **Uvicorn**: Servidor ASGI de alto rendimiento
- **Pydantic**: Validación de datos y serialización
- **PyYAML**: Procesamiento de archivos YAML con preguntas

### Herramientas de Procesamiento (Tools)
- **PyMuPDF**: Extracción de texto de archivos PDF
- **pdf2image**: Conversión de PDFs a imágenes para OCR
- **pytesseract**: Motor OCR para extraer texto de imágenes
- **Pillow**: Procesamiento y mejora de imágenes
- **pdfplumber**: Análisis avanzado de estructura PDF
- **numpy**: Operaciones numéricas para procesamiento de imágenes

## Herramientas de Extracción

El proyecto incluye herramientas específicas para procesar documentos oficiales de Madrid:

### Flujo Completo de Procesamiento

```bash
# 1. Extraer preguntas del PDF oficial de Madrid
python tools/extraction/madrid_extract_questions.py

# 2. Extraer respuestas usando OCR del PDF oficial de Madrid
python tools/extraction/madrid_extract_answers.py --exam-type PER --test-model TEST01

# 3. Combinar preguntas y respuestas
python tools/processing/madrid_merge_exam.py
```

### Extracción Avanzada de Respuestas

```bash
# Extraer todas las respuestas de todos los exámenes
python tools/extraction/madrid_extract_answers.py
python tools/extraction/madrid_extract_answers.py

# Extraer respuestas de un tipo específico de examen
python tools/extraction/madrid_extract_answers.py --exam-type PER

# Extraer respuestas de un modelo específico
python tools/extraction/madrid_extract_answers.py --exam-type PER --test-model TEST01

# Especificar archivo PDF personalizado
python tools/extraction/madrid_extract_answers.py --pdf-path "data/raw/answers/otro-examen.pdf" --exam-type PATRON_YATE
```

### Aplicar Respuestas Extraídas

```bash
# Aplicar respuestas OCR al archivo YAML
python tools/processing/madrid_merge_exam.py
```

**Tipos de examen soportados:**
- `PER`: Patrón de Embarcación de Recreo
- `PATRON_YATE`: Patrón de Yate  
- `CAPITAN_YATE`: Capitán de Yate
- `LICENCIA_NAVEGACION`: Licencia de Navegación

## Despliegue en Azure Web Apps
La aplicación está configurada para desplegarse directamente en Azure Web Apps usando el archivo `requirements.txt` y la estructura estándar de FastAPI.

## Configuración

La aplicación utiliza un sistema de configuración centralizada basado en variables de entorno. 

### Variables de Entorno

1. **Copiar el archivo de ejemplo:**
   ```bash
   cp .env.example .env
   ```

2. **Editar las variables según tu entorno:**
   ```bash
   # Configuración del servidor
   PER_HOST=0.0.0.0
   PER_PORT=8002
   PER_DEBUG=false
   
   # Rutas de archivos
   PER_DATA_DIR=data
   PER_EXAMS_DIR=data/exams
   
   # Configuración de exámenes
   PER_DEFAULT_NUM_QUESTIONS=45
   PER_EXAM_TTL_HOURS=2
   ```

### Configuración por Defecto

Si no se define ninguna variable de entorno, la aplicación utilizará los valores por defecto:
- **Puerto**: 8002
- **Host**: 0.0.0.0 (todas las interfaces)
- **Directorio de datos**: `data/`
- **Preguntas por examen**: 45
- **Tiempo de vida de exámenes**: 2 horas