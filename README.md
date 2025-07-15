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
│   │   ├── questions/       # Preguntas organizadas jerárquicamente
│   │   │   └── madrid/      # Preguntas por comunidad autónoma
│   │   │       ├── 2022/    # Exámenes del año 2022
│   │   │       ├── 2023/    # Exámenes del año 2023
│   │   │       ├── 2024/    # Exámenes del año 2024
│   │   │       └── 2025/    # Exámenes del año 2025
│   │   └── answers/         # Respuestas oficiales en formato JSON
│   │       └── madrid/      # Respuestas organizadas por comunidad
│   │           ├── 2022/    # Respuestas del año 2022
│   │           ├── 2023/    # Respuestas del año 2023
│   │           ├── 2024/    # Respuestas del año 2024
│   │           └── 2025/    # Respuestas del año 2025
│   ├── backups/             # Archivos YAML de respaldo (estructura antigua)
│   └── raw/                 # PDFs originales sin procesar
│       ├── questions/       # PDFs de preguntas oficiales organizados jerárquicamente
│       │   └── madrid/      # PDFs por comunidad autónoma
│       │       ├── 2022/    # PDFs del año 2022
│       │       ├── 2023/    # PDFs del año 2023
│       │       ├── 2024/    # PDFs del año 2024
│       │       └── 2025/    # PDFs del año 2025
│       └── answers/         # PDFs de respuestas oficiales organizados jerárquicamente
│           └── madrid/      # PDFs por comunidad autónoma
│               ├── 2022/    # PDFs del año 2022
│               ├── 2023/    # PDFs del año 2023
│               ├── 2024/    # PDFs del año 2024
│               └── 2025/    # PDFs del año 2025
├── static/                  # Frontend (HTML, CSS, JS)
├── tools/                   # Scripts de extracción y procesamiento
│   ├── extraction/          # Scripts de extracción de datos
│   │   ├── madrid_extract_questions.py   # Extractor de preguntas de PDFs
│   │   ├── madrid_extract_answers_v2.py  # Extractor OCR de respuestas
│   │   └── README.md        # Documentación de extracción
│   ├── processing/          # Scripts de procesamiento de datos
│   │   ├── madrid_apply_answers.py       # Aplicador de respuestas
│   │   └── README.md        # Documentación de procesamiento
│   └── README.md            # Documentación general de herramientas
├── extracted-answers/       # Respuestas extraídas por OCR (temporal)
├── .env.example             # Plantilla de variables de entorno
├── requirements.txt         # Dependencias completas
├── requirements-minimal.txt # Dependencias mínimas
└── README.md               # Este archivo
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

## Estructura de Datos

### Organización de Archivos YAML y JSON

Los archivos con las preguntas de examen (YAML) y respuestas (JSON) están organizados jerárquicamente:

```
data/exams/
├── questions/
│   └── madrid/                      # Comunidad autónoma
│       ├── 2022/                    # Año del examen
│       ├── 2023/                    # Año del examen
│       ├── 2024/                    # Año del examen
│       └── 2025/                    # Año del examen
└── answers/
    └── madrid/                      # Comunidad autónoma
        ├── 2022/                    # Año del examen
        ├── 2023/                    # Año del examen
        ├── 2024/                    # Año del examen
        └── 2025/                    # Año del examen
```

### Nomenclatura de Archivos

Los archivos siguen el mismo patrón para preguntas (YAML) y respuestas (JSON):

**Preguntas**: `per-test{XX}-{comunidad}-{año}-{convocatoria}.yaml`
**Respuestas**: `per-test{XX}-{comunidad}-{año}-{convocatoria}.json`

- **test**: Numeración secuencial (test01, test02, test03, test04)
- **comunidad**: Madrid, Valencia, Barcelona, etc.
- **año**: 2022, 2023, 2024, 2025...
- **convocatoria**: abril, junio, noviembre, diciembre, octubre

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
Extrae respuestas oficiales de PDFs usando reconocimiento óptico de caracteres. Es la versión robusta y actualizada del script para todos los exámenes oficiales.

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
# Resultado: data/exams/questions/madrid/2025/per-test01-madrid-2025-abril.yaml
python tools/extraction/madrid_extract_questions.py

# 2. Extraer respuestas usando OCR del PDF oficial
python tools/extraction/madrid_extract_answers_v2.py --exam-type PER --test-model TEST01

# 3. Combinar preguntas y respuestas
python tools/processing/madrid_apply_answers.py
```

#### Para otros años/comunidades/convocatorias:
```bash
# Ejemplo: Madrid 2024 noviembre test01
# 1. Extraer preguntas
# Resultado: data/exams/per-test01-madrid-2024-noviembre.yaml
python tools/extraction/madrid_extract_questions.py --input-file data/raw/questions/madrid-2024-noviembre.pdf --test-code 01

# 2. Extraer respuestas (especificando PDF correcto)
python tools/extraction/madrid_extract_answers_v2.py --input-file "data/raw/answers/madrid/2024/madrid-2024-noviembre.pdf"

# 3. Combinar datos
python tools/processing/madrid_apply_answers.py --input-file per-test01-madrid-2024-noviembre.json --target-file per-test01-madrid-2024-noviembre.yaml
```

#### Para Valencia 2024 junio (ejemplo):
```bash
# 1. Extraer preguntas
# Resultado: data/exams/per-test02-valencia-2024-junio.yaml
python tools/extraction/madrid_extract_questions.py --input-file data/raw/questions/valencia-2024-junio.pdf --test-code 02

# 2. Extraer respuestas
python tools/extraction/madrid_extract_answers_v2.py --input-file "data/raw/answers/valencia/2024/valencia-2024-junio.pdf"

# 3. Combinar datos
python tools/processing/madrid_apply_answers.py --input-file per-test02-valencia-2024-junio.json --target-file per-test02-valencia-2024-junio.yaml
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
python tools/extraction/madrid_extract_answers_v2.py --pdf-path "data/raw/answers/madrid/2023/madrid-2023-junio.pdf" --exam-type PATRON_YATE
```

### Aplicar Respuestas Extraídas

```bash
# Aplicar respuestas OCR al archivo YAML
python tools/processing/madrid_apply_answers.py
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
   PER_EXAMS_DIR=data/exams/questions
   PER_ANSWERS_DIR=data/exams/answers
   
   # Configuración de exámenes
   PER_DEFAULT_NUM_QUESTIONS=45
   PER_EXAM_TTL_HOURS=2
   ```

### Configuración por Defecto

Si no se define ninguna variable de entorno, la aplicación utilizará los valores por defecto:
- **Puerto**: 8002
- **Host**: 0.0.0.0 (todas las interfaces)
- **Directorio de datos**: `data/`
- **Directorio de preguntas**: `data/exams/questions/`
- **Directorio de respuestas**: `data/exams/answers/`
- **Preguntas por examen**: 45
- **Tiempo de vida de exámenes**: 2 horas