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
├── app/                     # Código de la aplicación
│   ├── main.py              # Punto de entrada de FastAPI
│   ├── models/              # Modelos Pydantic
│   ├── services/            # Lógica de negocio
│   └── routers/             # Endpoints de la API
├── config/                  # Configuración centralizada
│   ├── __init__.py          # Paquete de configuración
│   └── settings.py          # Configuración principal
├── data/                    # Archivos YAML con preguntas
│   ├── exams/               # Archivos YAML de exámenes procesados
│   │   └── answers/         # Respuestas oficiales en formato JSON
│   │       └── madrid/      # Respuestas organizadas por comunidad
│   │           ├── 2024/    # Respuestas del año 2024
│   │           └── 2025/    # Respuestas del año 2025
│   └── raw/                 # PDFs originales sin procesar
│       ├── questions/       # PDFs de preguntas oficiales
│       └── answers/         # PDFs de respuestas oficiales
├── static/                  # Frontend (HTML, CSS, JS)
├── tools/                   # Scripts de extracción y procesamiento
│   ├── extraction/          # Scripts de extracción de datos
│   │   ├── madrid_extract_questions.py   # Extractor de preguntas 
de PDFs
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
└── requirements-minimal.txt # Dependencias mínimas
├── extracted_answers/       # Respuestas extraídas por OCR
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

### Dependencias del Sistema (DevContainer)

El devcontainer instala automáticamente las siguientes dependencias del sistema necesarias para OCR:

#### 📦 Paquetes del Sistema

1. **poppler-utils**: Herramientas para manipular archivos PDF
   - Necesario para: `pdf2image` (conversión de PDF a imágenes)
   - Comandos: `pdfinfo`, `pdftoppm`, etc.

2. **tesseract-ocr**: Motor de OCR (Reconocimiento Óptico de Caracteres)
   - Necesario para: `pytesseract` (reconocimiento de texto en imágenes)
   - Versión: 4.1.1

3. **tesseract-ocr-spa**: Paquete de idioma español para Tesseract
   - Mejora la precisión del OCR para texto en español
   - Incluye modelos entrenados específicamente para español

#### 🚀 Instalación Automática

Las dependencias del sistema se instalan automáticamente cuando se crea el devcontainer:

```bash
sudo apt update && sudo apt install -y poppler-utils tesseract-ocr tesseract-ocr-spa && pip3 install --user -r requirements.txt
```

#### ✅ Verificación de Instalación

Para verificar que las dependencias están correctamente instaladas:

```bash
# Verificar poppler
pdfinfo --version

# Verificar tesseract
tesseract --version

# Verificar idiomas disponibles en tesseract
tesseract --list-langs
```

#### 🔧 Solución de Problemas

Si encuentras errores relacionados con:

- `PDFInfoNotInstalledError`: Instala `poppler-utils`
- `tesseract is not installed`: Instala `tesseract-ocr`
- Precisión baja en OCR español: Instala `tesseract-ocr-spa`

#### 🏗️ Reconstruir Devcontainer

Si necesitas aplicar estos cambios a un Codespace existente:

1. Abre la paleta de comandos (Ctrl+Shift+P)
2. Busca "Dev Containers: Rebuild Container"
3. Selecciona la opción para reconstruir

O simplemente crea un nuevo Codespace que tendrá automáticamente todas las dependencias instaladas.

## Herramientas de Extracción

El proyecto incluye herramientas especializadas para procesar documentos oficiales de diferentes comunidades:

### `madrid_extract_questions.py` - Extractor Parametrizable
**Completamente parametrizable** para extraer preguntas de diferentes comunidades, años y convocatorias.

#### Características:
- ✨ **Extracción parametrizable**: Soporte para diferentes comunidades autónomas
- 🔍 **Búsqueda inteligente de PDFs**: Encuentra automáticamente archivos basándose en parámetros
- 📂 **Múltiples opciones de salida**: Personaliza directorios y nombres de archivo
- 🔧 **Manejo robusto de errores**: Sugerencias y validaciones útiles

#### Parámetros principales:
- `--community`: Comunidad autónoma (Madrid, Valencia, Barcelona, etc.)
- `--year`: Año del examen (2024, 2025, etc.)
- `--call`: Convocatoria (abril, junio, noviembre, etc.)
- `--test`: Código del test (test01, test02, test03)
- `--pdf-file`: Archivo PDF específico
- `--output-file`: Archivo de salida personalizado

### `madrid_extract_answers_v2.py` - Extractor OCR
Extrae respuestas oficiales de PDFs usando reconocimiento óptico de caracteres. Usa la versión robusta y actualizada del script para todos los exámenes oficiales.

#### Características:
- 🤖 **OCR avanzado**: Reconocimiento óptico con preprocesamiento
- 🎯 **Filtros específicos**: Extrae solo el tipo de examen deseado
- ✅ **Detección automática**: Identifica respuestas anuladas
- 📋 **Múltiples formatos**: Soporte para diferentes layouts

#### Parámetros principales:
- `--exam-type`: Tipo de examen (PER, PATRON_YATE, etc.)
- `--test-model`: Modelo específico (TEST01, TEST02, etc.)
- `--pdf-path`: Ruta al PDF de respuestas
- `--output-dir`: Directorio de salida

### Flujo Completo de Procesamiento

#### Para Madrid 2025 abril (por defecto):
```bash
# 1. Extraer preguntas del PDF oficial
python tools/extraction/madrid_extract_questions.py

# 2. Extraer respuestas usando OCR del PDF oficial
python tools/extraction/madrid_extract_answers_v2.py --exam-type PER --test-model TEST01

# 3. Combinar preguntas y respuestas
python tools/processing/madrid_merge_exam.py
```

#### Para otros años/comunidades/convocatorias:
```bash
# Ejemplo: Madrid 2024 noviembre test01
# 1. Extraer preguntas
python tools/extraction/madrid_extract_questions.py --year 2024 --call noviembre --test test01

# 2. Extraer respuestas (especificando PDF correcto)
python tools/extraction/madrid_extract_answers_v2.py --exam-type PER --test-model TEST01 --pdf-path "data/raw/answers/madrid-2024-noviembre.pdf"

# 3. Combinar datos
python tools/processing/madrid_merge_exam.py
```

#### Para Valencia 2024 junio (ejemplo):
```bash
# 1. Extraer preguntas
python tools/extraction/madrid_extract_questions.py --community Valencia --year 2024 --call junio --test test02

# 2. Extraer respuestas
python tools/extraction/madrid_extract_answers_v2.py --exam-type PER --test-model TEST02 --pdf-path "data/raw/answers/valencia-2024-junio.pdf"

# 3. Combinar datos
python tools/processing/madrid_merge_exam.py
```

### Extracción Avanzada de Respuestas

```bash
# Extraer todas las respuestas de todos los exámenes
python tools/extraction/madrid_extract_answers_v2.py

# Extraer respuestas de un tipo específico de examen
python tools/extraction/madrid_extract_answers_v2.py --exam-type PER

# Extraer respuestas de un modelo específico
python tools/extraction/madrid_extract_answers_v2.py --exam-type PER --test-model TEST01

# Especificar archivo PDF personalizado
python tools/extraction/madrid_extract_answers_v2.py --pdf-path "data/raw/answers/otro-examen.pdf" --exam-type PATRON_YATE
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