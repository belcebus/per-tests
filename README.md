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
├── tests/                   # Suite de pruebas automatizadas
│   ├── conftest.py          # Configuración y fixtures compartidas
│   ├── fixtures/            # Datos de prueba reutilizables
│   ├── unit/                # Tests unitarios
│   │   ├── test_models.py       # Tests de modelos Pydantic
│   │   ├── test_api_endpoints.py # Tests de endpoints FastAPI
│   │   └── test_question_loader.py # Tests del cargador de preguntas
│   └── integration/         # Tests de integración (futuro)
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
│   ├── utils/               # Herramientas de utilidad y verificación
│   │   ├── check_exam_consistency.py     # Verificador de consistencia
│   │   └── README.md        # Documentación de utilidades
│   └── README.md            # Documentación general de herramientas
├── extracted-answers/       # Respuestas extraídas por OCR (temporal)
├── pytest.ini              # Configuración de pytest
├── .env.example             # Plantilla de variables de entorno
├── requirements.txt         # Dependencias completas
├── requirements-minimal.txt # Dependencias mínimas
└── README.md               # Este archivo
```

## Instalación y Ejecución

### Opción 1: Instalación Completa (Recomendada)
Incluye todas las dependencias para la aplicación web, las herramientas de procesamiento y el framework de testing:

```bash
pip install -r requirements.txt
```

### Opción 2: Instalación Mínima (Solo Aplicación Web)
Solo las dependencias necesarias para ejecutar el servidor web (sin herramientas de procesamiento ni tests):

```bash
pip install -r requirements-minimal.txt
```

**Nota**: Para ejecutar tests en la instalación mínima, instalar dependencias adicionales:
```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock httpx
```

### Ejecutar la Aplicación

```bash
uvicorn app.main:app --reload
```

### Accesos Disponibles
- API: http://localhost:8000
- Documentación: http://localhost:8000/docs
- Cliente Web: http://localhost:8000/static/index.html

## Testing

### Descripción General
El proyecto incluye una suite completa de pruebas automatizadas para garantizar la calidad y funcionamiento correcto de la aplicación. Los tests están organizados en una estructura jerárquica que facilita el mantenimiento y la ejecución selectiva.

### Estructura de Tests

```
tests/
├── conftest.py              # Configuración global y fixtures compartidas
├── fixtures/                # Datos de prueba reutilizables
├── unit/                    # Tests unitarios (componentes aislados)
│   ├── test_models.py       # Validación de modelos Pydantic
│   ├── test_api_endpoints.py # Tests de endpoints FastAPI
│   └── test_question_loader.py # Tests del servicio de carga de preguntas
└── integration/             # Tests de integración (sistema completo)
```

### Tipos de Tests

#### 🔬 **Tests Unitarios** (`tests/unit/`)
Verifican el funcionamiento de componentes individuales de forma aislada:

- **`test_models.py`**: Validación de modelos Pydantic ✅
  - QuestionMetadata: Metadatos de exámenes (9/9 tests pasan)
  - Question: Estructura de preguntas (todas las validaciones funcionan)
  - ExamGenerationRequest: Solicitudes de generación de exámenes (todas funcionan)

- **`test_api_endpoints.py`**: Tests de endpoints de la API FastAPI ⚠️
  - Generación de exámenes aleatorios (requiere datos de prueba)
  - Corrección de exámenes enviados (funcionalidad parcial)
  - Endpoints de información y salud (básicos funcionan)
  - Manejo de errores HTTP (algunos ajustes necesarios)

- **`test_question_loader.py`**: Tests del servicio de carga de preguntas ⚠️
  - Carga de archivos YAML (requiere actualización por cambios en API)
  - Validación de estructura de datos (métodos privados cambiaron)
  - Organización por comunidades y categorías (funciona con datos reales)
  - Manejo de errores y archivos corruptos (parcialmente funcional)

#### 🔗 **Tests de Integración** (`tests/integration/`)
Verifican el funcionamiento del sistema completo con componentes reales (planificado para futuras versiones).

### Configuración de Tests

La configuración se encuentra en:
- **`pytest.ini`**: Configuración principal de pytest
- **`conftest.py`**: Fixtures compartidas y setup de tests

#### Markers Disponibles
- `@pytest.mark.unit`: Tests unitarios
- `@pytest.mark.integration`: Tests de integración  
- `@pytest.mark.api`: Tests específicos de API
- `@pytest.mark.slow`: Tests que requieren más tiempo

### Ejecución de Tests

#### Ejecutar Todos los Tests
```bash
pytest
```

#### Ejecutar Tests por Categoría
```bash
# Solo tests unitarios
pytest -m unit

# Solo tests de API
pytest -m api

# Excluir tests lentos
pytest -m "not slow"
```

#### Ejecutar Tests Específicos
```bash
# Un archivo específico
pytest tests/unit/test_models.py

# Una clase específica
pytest tests/unit/test_models.py::TestQuestionMetadata

# Un test específico
pytest tests/unit/test_models.py::TestQuestionMetadata::test_valid_metadata
```

#### Ejecución con Información Detallada
```bash
# Mostrar información detallada
pytest -v

# Mostrar output de print()
pytest -s

# Mostrar resumen de cobertura
pytest --cov=app

# Combinar opciones
pytest -v -s --cov=app tests/unit/
```

#### Ejecución en Modo de Desarrollo
```bash
# Parar en el primer fallo
pytest -x

# Ejecutar solo tests que fallaron en la última ejecución
pytest --lf

# Ejecutar tests en paralelo (requiere pytest-xdist)
pytest -n auto
```

#### Ejemplos Prácticos

```bash
# Verificar que los modelos funcionan correctamente (debería pasar)
pytest tests/unit/test_models.py -v

# Ejecutar solo tests rápidos (excluyendo lentos)
pytest -m "not slow" -v

# Generar reporte de cobertura HTML
pytest --cov=app --cov-report=html

# Ejecutar tests con logging detallado
pytest -v -s --log-cli-level=DEBUG

# Establecer umbral mínimo de cobertura
pytest --cov=app --cov-fail-under=80

# Mostrar líneas específicas no cubiertas
pytest --cov=app --cov-report=term-missing
```

### Medición de Completitud de Tests

#### 📊 **Cobertura de Código (Code Coverage)**

La cobertura de código es la métrica principal para medir la completitud de tests:

```bash
# Cobertura básica
pytest --cov=app

# Cobertura con detalles de líneas no cubiertas
pytest --cov=app --cov-report=term-missing

# Reporte HTML interactivo
pytest --cov=app --cov-report=html
# Ver en: htmlcov/index.html

# Establecer umbral mínimo (falla si no se alcanza)
pytest --cov=app --cov-fail-under=80
```

#### 🎯 **Objetivos de Cobertura Recomendados**

- **Modelos Pydantic**: 100% ✅ (Ya conseguido)
- **Servicios críticos**: 90%+ ⚠️ (Actualmente: 26% exam_service, 61% question_loader)
- **Routers/Endpoints**: 80%+ ✅ (Actualmente: 76%)
- **Configuración**: 70%+ ✅ 
- **Total del proyecto**: 80%+ ⚠️ (Actualmente: 59%)

#### 🔍 **Estado Actual de Cobertura**

```
📊 COBERTURA TOTAL: 59% (Mejorable)

Por módulos:
✅ app/models/schemas.py         100%  (Excelente)
🔶 app/routers/exams.py          76%   (Bueno)
🔶 app/services/question_loader.py  61%   (Aceptable)
🔶 app/main.py                   59%   (Mejorable)
❌ app/services/exam_service.py  26%   (Crítico - Requiere atención)

🚨 Áreas críticas que requieren más tests:
- Lógica de generación de exámenes (exam_service.py)
- Corrección automática de respuestas
- Manejo de errores en servicios
- Endpoints de API complejos
```

#### 🧪 **Métricas Adicionales de Calidad**

Además de la cobertura, considera estas métricas:

```bash
# Complejidad ciclomática (requiere radon)
pip install radon
radon cc app/ -a

# Análisis de código estático (requiere flake8)
pip install flake8
flake8 app/

# Detección de código duplicado (requiere pylint)
pip install pylint
pylint app/

# Tests de mutación (requiere mutmut)
pip install mutmut
mutmut run
```

#### 📋 **Checklist de Completitud**

**Tests Unitarios:**
- [x] Modelos Pydantic (100%)
- [x] Validaciones básicas
- [ ] Servicios críticos (exam_service: 26% ⚠️)
- [ ] Lógica de negocio compleja
- [ ] Manejo de errores

**Tests de API:**
- [x] Endpoints básicos (health, info)
- [ ] Generación de exámenes
- [ ] Corrección de exámenes
- [ ] Validación de entrada
- [ ] Manejo de errores HTTP

**Tests de Integración:**
- [ ] Flujo completo de examen
- [ ] Interacción entre servicios
- [ ] Persistencia de datos

#### 🎯 **Plan de Mejora Sugerido**

1. **Prioridad Alta** (Semana 1):
   ```bash
   # Objetivo: Alcanzar 80% en exam_service.py
   - Tests para generate_exam()
   - Tests para correct_exam() 
   - Tests de manejo de errores
   ```

2. **Prioridad Media** (Semana 2):
   ```bash
   # Objetivo: Alcanzar 85% en question_loader.py
   - Tests para load_all_questions()
   - Tests para get_stats()
   - Tests de validación de archivos
   ```

3. **Prioridad Baja** (Semana 3):
   ```bash
   # Objetivo: Tests de integración
   - Flujo completo de generación-corrección
   - Tests de rendimiento
   - Tests end-to-end
   ```

### Fixtures Disponibles

El archivo `conftest.py` proporciona fixtures reutilizables:

- **`client`**: Cliente de test síncrono para FastAPI
- **`async_client`**: Cliente de test asíncrono para FastAPI  
- **`temp_dir`**: Directorio temporal para tests
- **`mock_question_loader`**: Mock del servicio de carga de preguntas
- **`sample_questions`**: Datos de prueba con preguntas de ejemplo

### Estadísticas de Tests

Estado actual de la suite de tests:
- **47 tests** en total
- **Tests que pasan**: 20 tests
- **Tests que fallan**: 27 tests (principalmente debido a incompatibilidades con la API actualizada)
- **Cobertura**: Modelos Pydantic (✅), endpoints FastAPI (⚠️ parcial), servicios de carga (⚠️ requiere actualización)

### Integración Continua

Los tests se ejecutan automáticamente en:
- Commits y pull requests
- Despliegues en Azure Web Apps
- Desarrollo local con git hooks (opcional)

### Contribuir con Tests

Al añadir nuevas funcionalidades:

1. **Escribir tests unitarios** para nuevos modelos/servicios
2. **Seguir la convención de nombres**: `test_*.py`
3. **Usar fixtures** existentes cuando sea posible
4. **Añadir markers** apropiados (`@pytest.mark.unit`, etc.)
5. **Documentar** tests complejos con docstrings
6. **Actualizar estadísticas** en este README cuando se añadan tests

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

### Testing
- **pytest**: Framework de testing moderno y potente
- **pytest-asyncio**: Soporte para tests asíncronos
- **pytest-cov**: Generación de reportes de cobertura de código
- **pytest-mock**: Utilities para mocking en tests
- **httpx**: Cliente HTTP asíncrono para tests de API

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
- `--input-file`: Ruta al PDF de respuestas (obligatorio)
- `--output-dir`: Directorio de salida (opcional)
- `--verbose`: Información detallada del procesamiento (opcional)

### Flujo Completo de Procesamiento

#### Para Madrid 2025 abril (por defecto):
```bash
# 1. Extraer preguntas del PDF oficial
# Resultado: data/exams/questions/madrid/2025/per-test01-madrid-2025-abril.yaml
python tools/extraction/madrid_extract_questions.py --input-file data/raw/questions/madrid/2025/madrid-2025-abril.pdf --test-code 01

# 2. Extraer respuestas usando OCR del PDF oficial
python tools/extraction/madrid_extract_answers_v2.py --input-file data/raw/answers/madrid/2025/madrid-2025-abril.pdf

# 3. Combinar preguntas y respuestas
python tools/processing/madrid_apply_answers.py --input-file per-test01-madrid-2025-abril.json --target-file per-test01-madrid-2025-abril.yaml
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
# Extraer respuestas de un PDF específico
python tools/extraction/madrid_extract_answers_v2.py --input-file "data/raw/answers/madrid/2025/madrid-2025-abril.pdf"

# Extraer respuestas con directorio personalizado
python tools/extraction/madrid_extract_answers_v2.py --input-file "data/raw/answers/madrid/2024/madrid-2024-junio.pdf" --output-dir "mis_respuestas"

# Extraer respuestas con información detallada
python tools/extraction/madrid_extract_answers_v2.py --input-file "data/raw/answers/madrid/2023/madrid-2023-noviembre.pdf" --verbose
```

### Aplicar Respuestas Extraídas

```bash
# Aplicar respuestas OCR al archivo YAML (con auto-detección)
python tools/processing/madrid_apply_answers.py --verbose

# Aplicar respuestas especificando archivos
python tools/processing/madrid_apply_answers.py --input-file respuestas.json --target-file examen.yaml --verbose
```

**Nota**: El script detecta automáticamente el tipo de examen desde el contenido del PDF usando OCR.

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