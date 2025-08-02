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
├── .github/
│   └── workflows/
│       ├── ci.yml           # Workflow de CI (tests)
│       └── security.yml     # Workflow de análisis de seguridad (Semgrep)
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
│   │   ├── README.md        # Documentación de fixtures
│   │   ├── sample_exam.yaml # Examen de muestra para tests
│   │   └── sample_answers.json # Respuestas de muestra para tests
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

├── extracted-answers/       # Respuestas extraídas por OCR (temporal)
├── Makefile                 # Comandos automatizados para testing y desarrollo
├── pyproject.toml           # Configuración moderna: proyecto, dependencias, pytest, coverage
└── README.md                # Este archivo
```

## Instalación y Ejecución

### 🚀 **Instalación Moderna (Recomendada)**

El proyecto utiliza `pyproject.toml` para gestión moderna de dependencias. Puedes instalar solo lo que necesitas:

```bash
# Instalación básica (solo aplicación web)
make install
# o manualmente:
pip install -e .

# Instalación para desarrollo (tests, cobertura, etc.)
make install-dev
# o manualmente:
pip install -e ".[dev]"

# Instalación con herramientas de procesamiento (OCR, PDFs)
make install-tools
# o manualmente:
pip install -e ".[tools]"

# Instalación para análisis de seguridad (Semgrep)
make install-security
# o manualmente:
pip install -e ".[security]"

# Instalación completa (desarrollo + herramientas)
make install-full
# o manualmente:
pip install -e ".[full]"

# Instalación para linting y análisis estático
make install-lint
# o manualmente:
pip install -e ".[lint]"
```

### 📦 **Instalación Legacy (Solo si es necesario)**

Para sistemas muy antiguos que no soporten `pyproject.toml`:

```bash
# Generar requirements.txt desde pyproject.toml si es necesario
pip install pip-tools
pip-compile pyproject.toml
pip install -r requirements.txt
```

### ⚡ **Instalación Rápida para Desarrollo**

```bash
# Un solo comando para desarrollo completo
make install-dev && make test-fast
```

## 🛠️ **Makefile - Herramienta de Desarrollo**

El proyecto incluye un Makefile completo que simplifica todas las tareas de desarrollo, testing y despliegue. Es la herramienta principal recomendada para trabajar con el proyecto.

### **📋 Comandos Disponibles**

#### **Comandos útiles y calidad de código:**
   - `make install-dev` — instala dependencias de desarrollo
   - `make test-fast` — ejecuta todos los tests sin cobertura (rápido)
   - `make test-unit` — ejecuta solo tests unitarios
   - `make test-integration` — ejecuta solo tests de integración
   - `make test-api` — ejecuta solo tests de API
   - `make test-cov` — ejecuta tests con cobertura en terminal
   - `make test-cov-html` — genera reporte HTML de cobertura
   - `make test-cov-xml` — genera reporte XML de cobertura
   - `make test-cov-full` — genera reportes HTML+XML de cobertura
   - `make test-cov-strict` — ejecuta tests con cobertura mínima (95%)
   - `make test-ci` — ejecuta tests para CI/CD (con timeout)
   - `make quality` — ejecuta linters y analizadores (flake8, pylint, black, isort, radon, mypy)
   - `make security` — ejecuta análisis de seguridad del código (semgrep)
   - `make run` — inicia la aplicación (configuración por defecto)
   - `make run-prod` — inicia en modo producción (4 workers)
   - `make run-azure` — inicia optimizado para Azure (1 worker)
   - `make run-debug` — inicia con debug habilitado
   - `make run-local` — inicia solo en localhost
   - `make run-custom` — inicia con variables de entorno personalizadas
   - `make clean` — limpia archivos temporales y de cobertura
   - `make clean-venv` — elimina el entorno virtual

   **Ejemplos:**
   - `make install-dev`                  # Instalación para desarrollo
   - `make test-fast`                    # Durante desarrollo
   - `make test-cov`                     # Para verificar cobertura
   - `make quality`                      # Análisis de calidad de código
   - `make test-cov-html`                # Para generar reporte visual
   - `make run`                          # Aplicación con configuración por defecto
   - `PER_PORT=9000 make run`            # Cambiar puerto
   - `PER_HOST=localhost make run-local` # Localhost en puerto personalizado


#### **Testing Rápido (Desarrollo):**
```bash
make test-fast       # Tests sin cobertura (7-8 segundos)
make test-unit       # Solo tests unitarios
make test-api        # Solo tests de API
```

#### **Testing con Cobertura:**
```bash
make test-cov        # Cobertura en terminal
make test-cov-html   # + Reporte HTML visual
make test-cov-xml    # + Reporte XML (CI/CD)
make test-cov-full   # HTML + XML completo
```

#### **Análisis de Seguridad:**
```bash
make security        # Ejecuta Semgrep con las reglas oficiales
# Requiere tener instalado el perfil [security]
```

#### **Ejecución de Aplicación:**
```bash
make run            # Desarrollo (config/settings.py)
make run-debug      # + Debug detallado
make run-local      # Solo localhost
make run-azure      # Optimizado para Azure
make run-prod       # Producción (4 workers)
make run-custom     # Variables de entorno personalizadas
```

#### **Mantenimiento:**
```bash
make clean          # Limpiar archivos temporales
make help           # Ver todos los comandos disponibles
```

### **💡 Ejemplos de Uso**

```bash
# Flujo típico de desarrollo
make install-dev                    # Configurar entorno
make test-fast                      # Verificar que todo funciona
make run                           # Ejecutar aplicación

# Verificar calidad antes de commit
make test-cov                      # Ver cobertura actual
make test-cov-html                 # Generar reporte detallado

# Personalizar configuración
PER_PORT=9000 make run             # Cambiar puerto
PER_HOST=localhost make run-local  # Solo localhost
```

### 🖥️ **Ejecutar la Aplicación**

El proyecto está optimizado para desplegarse como servidor API en Azure. Utiliza configuración centralizada en `config/settings.py` y comandos Makefile para diferentes escenarios.

#### **🚀 Para Desarrollo (Recomendado)**

```bash
# Usar configuración por defecto (puerto 8002, auto-reload)
make run

# Con debug detallado
make run-debug

# Solo accesible desde localhost
make run-local

# Con configuración personalizada
PER_PORT=9000 make run
PER_HOST=localhost make run-custom
```

#### **☁️ Para Despliegue en Azure**

```bash
# Optimizado para Azure App Service (1 worker)
make run-azure

# Producción local (4 workers)
make run-prod
```

#### **⚙️ Métodos Alternativos**

```bash
# Ejecución directa con Python
python app/main.py

# Control total con uvicorn
uvicorn app.main:app --reload --port 8000
```

#### **📋 Configuración Centralizada**

Configuración por defecto en `config/settings.py`:
- **Puerto**: 8002
- **Host**: 0.0.0.0 (accesible externamente)
- **Auto-reload**: Habilitado en desarrollo
- **Log level**: info

**Variables de entorno disponibles:**
- `PER_PORT`: Puerto del servidor
- `PER_HOST`: Host del servidor  
- `PER_RELOAD`: Auto-reload (true/false)
- `PER_LOG_LEVEL`: Nivel de logging (debug/info/warning/error)

### 🌐 **Accesos Disponibles**

**Con configuración por defecto (`make run`):**
- **API Principal**: http://localhost:8002
- **Documentación Interactiva**: http://localhost:8002/docs
- **Cliente Web**: http://localhost:8002/static/index.html
- **Health Check**: http://localhost:8002/health

**Con comandos de producción (`make run-prod`, `make run-azure`):**
- **API Principal**: http://localhost:8000
- **Documentación**: http://localhost:8000/docs
- **Cliente Web**: http://localhost:8000/static/index.html

## Funcionalidades

La aplicación PER Tests ofrece tres tipos de exámenes para la preparación del Patrón de Embarcaciones de Recreo, cada uno diseñado para diferentes necesidades de estudio y práctica.

### 🎯 **Tipos de Exámenes Disponibles**

#### 1. **Examen de Práctica** 📚
Exámenes personalizables para práctica general con filtros avanzados.

**Características:**
- **Filtros disponibles**: Categorías, años, comunidades autónomas
- **Número de preguntas**: Configurable (1-100 preguntas)
- **Generación**: Aleatoria basada en filtros seleccionados
- **Uso recomendado**: Estudio por temas específicos o práctica general

**Ejemplo de uso:**
- Practicar solo preguntas de "Seguridad" de los años 2023-2024
- Examen mixto de todas las categorías de Madrid
- Práctica intensiva con 50 preguntas aleatorias

#### 2. **Examen Simulacro** ⏱️
Simulación completa del examen oficial con condiciones reales.

**Características:**
- **Formato oficial**: 45 preguntas obligatorias
- **Tiempo limitado**: 60 minutos (como el examen oficial)
- **Distribución proporcional**: Preguntas balanceadas por categorías
- **Corrección automática**: Nota sobre 10 y análisis detallado
- **Uso recomendado**: Preparación final y evaluación de conocimientos

**Detalles del simulacro:**
- Replica las condiciones del examen oficial PER
- Cronómetro visible con alertas de tiempo
- Imposible modificar respuestas una vez finalizado
- Estadísticas detalladas por categoría

#### 3. **Examen Específico** 🎯 *(NUEVO)*
Selección y realización de exámenes oficiales concretos de convocatorias específicas.

**Características:**
- **Selección precisa**: Elige un examen oficial específico
- **Navegación en cascada**: Comunidad → Año → Convocatoria → Modelo
- **Exámenes oficiales**: Preguntas exactas de convocatorias reales
- **Trazabilidad completa**: Información del examen original

**Flujo de selección:**
1. **Comunidad Autónoma**: Selecciona la región (ej: Madrid)
2. **Año**: Elige el año de la convocatoria (2019-2025)
3. **Convocatoria**: Selecciona el período (abril, junio, octubre, noviembre, diciembre)
4. **Modelo de Examen**: Elige el modelo específico (Test01, Test02, Test03, Test04, etc.)

**Ejemplo de exámenes disponibles:**
- Madrid 2024 → Abril → Test01 (45 preguntas)
- Madrid 2023 → Noviembre → Test03 (45 preguntas)
- Madrid 2022 → Junio → Test02 (45 preguntas)

### 🛠️ **Funcionalidades Técnicas**

#### **API REST Endpoints**
- `GET /api/exams/info` - Información general del sistema
- `GET /api/exams/categories` - Categorías y datos para formularios
- `GET /api/exams/metadata` - Metadatos para exámenes específicos
- `GET /api/exams/available-exams` - Modelos disponibles por criterios
- `POST /api/exams/generate` - Generar examen de práctica/simulacro
- `POST /api/exams/generate-specific` - Generar examen específico
- `POST /api/exams/correct` - Corregir y evaluar examen

#### **Cliente Web Interactivo**
- **Interfaz moderna**: HTML5, CSS3, JavaScript ES6+
- **Responsive design**: Adaptable a móviles y tablets
- **Navegación intuitiva**: Pasos claros para cada tipo de examen
- **Resultados detallados**: Análisis por categorías y estadísticas

#### **Sistema de Corrección Avanzado**
- **Evaluación automática**: Corrección instantánea al finalizar
- **Análisis por categorías**: Rendimiento detallado por tema
- **Estadísticas completas**: Porcentaje global y por áreas
- **Recomendaciones**: Identificación de áreas de mejora

### 📊 **Base de Datos de Preguntas**

**Cobertura actual:**
- **Total de preguntas**: 3,285 preguntas oficiales
- **Categorías**: 11 categorías del temario PER
- **Años disponibles**: 2019-2025 (7 años de convocatorias)
- **Comunidades**: Madrid (expansión a otras CCAA planificada)
- **Convocatorias**: Abril, Junio, Octubre, Noviembre, Diciembre

**Categorías incluidas:**
1. **Nomenclatura náutica** - Terminología básica de embarcaciones
2. **Elementos de amarre y fondeo** - Cabos, anclas y equipamiento
3. **Seguridad** - Equipos de seguridad y procedimientos
4. **Legislación** - Normativa marítima y administrativa
5. **Balizamiento** - Señalización marítima y costera
6. **Reglamento (RIPA)** - Reglamento Internacional para Prevenir Abordajes
7. **Maniobra y navegación** - Técnicas de navegación y maniobra
8. **Emergencias en la mar** - Procedimientos de emergencia
9. **Meteorología** - Tiempo, clima y fenómenos meteorológicos
10. **Teoría de la navegación** - Conceptos navegación y posicionamiento
11. **Carta de navegación** - Interpretación y uso de cartas náuticas

## Testing

### 🏆 **Logros de Calidad Conseguidos**

**Estado actual: EXCELENTE** ✨
- 🎯 **97% de cobertura total** (Objetivo 80% superado)
- ✅ **100 tests ejecutándose** con 100% de éxito
- 🧹 **Código limpio**: Eliminadas 68 líneas de código muerto
- 📊 **Métricas sobresalientes** en todos los módulos críticos

**Mejoras recientes destacadas:**
- `question_loader.py`: 61% → **100%** (+39 puntos)
- `exam_service.py`: 26% → **98%** (+72 puntos)
- `main.py`: 59% → **95%** (+36 puntos)
- Suite de tests: 47 → **100 tests** (+53 tests nuevos)
- Fallos: 27 → **0 fallos** (100% éxito)

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

La configuración se encuentra centralizada en:
- **`pyproject.toml`**: Configuración principal de pytest, coverage y herramientas
- **`conftest.py`**: Fixtures compartidas y setup de tests

#### Markers Disponibles
- `@pytest.mark.unit`: Tests unitarios
- `@pytest.mark.integration`: Tests de integración  
- `@pytest.mark.api`: Tests específicos de API
- `@pytest.mark.slow`: Tests que requieren más tiempo

### Ejecución de Tests

#### 🚀 **Tests Rápidos (Recomendado para Desarrollo)**

```bash
# Ejecutar todos los tests sin cobertura (más rápido)
make test-fast
# o simplemente
pytest

# Tests por categoría
make test-unit      # Solo tests unitarios
make test-api       # Solo tests de API
pytest -m unit      # Alternativa directa
```

#### 📊 **Tests con Cobertura (Para Verificación)**

```bash
# Cobertura básica en terminal
make test-cov
# o
pytest --cov=app --cov-report=term-missing

# Cobertura con reporte HTML visual
make test-cov-html
# Abre: coverage_html/index.html

# Cobertura con reporte XML (para CI/CD)
make test-cov-xml

# Cobertura completa (HTML + XML)
make test-cov-full
```

#### 🎯 **Tests Específicos**
```bash
# Un archivo específico
pytest tests/unit/test_models.py

# Una clase específica
pytest tests/unit/test_models.py::TestQuestionMetadata

# Un test específico
pytest tests/unit/test_models.py::TestQuestionMetadata::test_valid_metadata

# Excluir tests lentos
pytest -m "not slow"
```

#### ⚡ **Opciones de Desarrollo**
```bash
# Parar en el primer fallo
pytest -x

# Ejecutar solo tests que fallaron
pytest --lf

# Tests en paralelo (requiere pytest-xdist)
pytest -n auto

# Mostrar output detallado
pytest -v -s
```

#### 🔧 **Comandos Avanzados**

```bash
# Tests con umbral de cobertura estricto
make test-cov-strict

# Limpiar archivos de cobertura
make clean

# Ver todos los comandos disponibles
make help
```

#### 💡 **Ejemplos de Uso Según Contexto**

```bash
# 🏃‍♂️ Durante desarrollo activo (rápido)
make test-fast

# 🔍 Verificar un módulo específico
pytest tests/unit/test_models.py -v

# 📊 Verificar cobertura antes de commit
make test-cov

# 🎯 Verificar que todos los objetivos se cumplen
make test-cov-strict

# 🤖 Para CI/CD automático
make test-ci

# 🧹 Limpiar después de desarrollo
make clean
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

- **Modelos Pydantic**: 100% ✅ (Conseguido)
- **Servicios críticos**: 90%+ ✅ (Conseguido: 98% exam_service, 100% question_loader)
- **Routers/Endpoints**: 80%+ ✅ (Conseguido: 85%)
- **Configuración**: 70%+ ✅ (Conseguido: 95% main.py)
- **Total del proyecto**: 80%+ ✅ (Conseguido: 97% - ¡SUPERADO!)

#### 🔍 **Estado Actual de Cobertura**

```
🏆 COBERTURA TOTAL: 97% (EXCELENTE - Objetivo 80% superado)

Por módulos:
✅ app/models/schemas.py         100%  (Perfecto)
✅ app/services/question_loader.py 100%  (Perfecto - Mejorado desde 61%)
✅ app/services/exam_service.py   98%   (Excelente - Mejorado desde 26%)
✅ app/main.py                    95%   (Muy bueno - Mejorado desde 59%)
✅ app/routers/exams.py           85%   (Muy bueno - Mejorado desde 76%)

🎯 Logros destacados:
- Eliminación de código muerto (68 líneas en question_loader.py)
- Mejora masiva en exam_service.py (+72 puntos de cobertura)
- Mejora significativa en main.py (+36 puntos de cobertura)
- 100 tests ejecutándose con 100% de éxito
- Total de 398 líneas de código, solo 11 sin cubrir
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
- [x] Modelos Pydantic (100%) ✅
- [x] Validaciones básicas ✅
- [x] Servicios críticos (98% exam_service, 100% question_loader) ✅
- [x] Lógica de negocio compleja ✅
- [x] Manejo de errores básicos ✅

**Tests de API:**
- [x] Endpoints básicos (health, info) ✅
- [x] Generación de exámenes ✅
- [x] Corrección de exámenes ✅
- [x] Validación de entrada ✅
- [ ] Manejo de errores HTTP complejos ⚠️

**Tests de Integración:**
- [ ] Flujo completo de examen ⚠️
- [ ] Interacción entre servicios ⚠️
- [ ] Persistencia de datos ⚠️

#### 🎯 **Plan de Mejora Actualizado**

🏆 **OBJETIVOS PRINCIPALES CONSEGUIDOS** (97% cobertura total)

**Completado recientemente:**
- ✅ Eliminación de código muerto en question_loader.py (-68 líneas)
- ✅ Cobertura 100% en servicios críticos
- ✅ Suite de 100 tests con 100% éxito
- ✅ Superación del objetivo del 80% de cobertura

**Próximas prioridades:**

1. **Prioridad Alta** (Próximas semanas):
   ```bash
   # Objetivo: Tests de integración y casos edge
   - Tests end-to-end del flujo completo de examen
   - Manejo de errores HTTP complejos
   - Tests de rendimiento y carga
   ```

2. **Prioridad Media** (Futuro):
   ```bash
   # Objetivo: Optimización y métricas avanzadas
   - Análisis de complejidad ciclomática
   - Tests de mutación para validar calidad
   - Integración continua mejorada
   ```

3. **Prioridad Baja** (Opcional):
   ```bash
   # Objetivo: Herramientas adicionales
   - Análisis estático de código (flake8, pylint)
   - Documentación automática de API
   - Monitorización de rendimiento
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
- **100 tests** en total ✅ (Incremento desde 47 tests)
- **Tests que pasan**: 100 tests (100% éxito) ✅
- **Tests que fallan**: 0 tests ✅ (Reducción desde 27 fallos)
- **Cobertura**: 97% total ✅ (Incremento masivo desde 59%)
  - Modelos Pydantic: 100% ✅
  - Servicios: exam_service 98%, question_loader 100% ✅
  - Endpoints FastAPI: 85% ✅
  - Configuración: 95% ✅

**Mejoras recientes conseguidas:**
- 🧹 Eliminación de 68 líneas de código muerto
- 📈 Mejora de +38 puntos en cobertura total (59% → 97%)
- 🧪 Duplicación de número de tests (47 → 100)
- ✅ Reducción de fallos a cero (27 → 0)
- 🎯 Superación del objetivo del 80% de cobertura

### Integración Continua

El proyecto incluye dos workflows de GitHub Actions:

- **CI**: Ejecuta automáticamente los tests en cada pull request a la rama `main`, usando solo dependencias de desarrollo ([dev]). Puedes ver el workflow en `.github/workflows/ci.yml`.
- **Security**: Ejecuta el análisis de seguridad (Semgrep) en un workflow independiente, usando solo dependencias de seguridad ([security]).

Esto permite que la instalación de dependencias en CI sea más rápida y modular, y que el análisis de seguridad se ejecute solo cuando sea necesario.

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

### Perfiles de dependencias

- **[dev]**: Testing y desarrollo (pytest, coverage, httpx, etc.)
- **[tools]**: Procesamiento de PDFs e imágenes (PyMuPDF, pdf2image, pytesseract, Pillow, pdfplumber, numpy)
- **[security]**: Análisis de seguridad (Semgrep)
- **[lint]**: Linting y análisis estático (flake8, black, isort, mypy, radon, pylint)
- **[full]**: Todo lo anterior junto

### Core (Aplicación Web)
- **FastAPI**: Framework web moderno para APIs REST
- **Uvicorn**: Servidor ASGI de alto rendimiento
- **Pydantic**: Validación de datos y serialización
- **PyYAML**: Procesamiento de archivos YAML con preguntas

### Testing ([dev])
- **pytest**: Framework de testing moderno y potente
- **pytest-asyncio**: Soporte para tests asíncronos
- **pytest-cov**: Generación de reportes de cobertura de código
- **pytest-mock**: Utilities para mocking en tests
- **httpx**: Cliente HTTP asíncrono para tests de API
- **asgi_lifespan**: Soporte para tests de ciclo de vida ASGI

### Herramientas de Procesamiento ([tools])
- **PyMuPDF**: Extracción de texto de archivos PDF
- **pdf2image**: Conversión de PDFs a imágenes para OCR
- **pytesseract**: Motor OCR para extraer texto de imágenes
- **Pillow**: Procesamiento y mejora de imágenes
- **pdfplumber**: Análisis avanzado de estructura PDF
- **numpy**: Operaciones numéricas para procesamiento de imágenes

### Análisis de Seguridad ([security])
- **semgrep**: Análisis de seguridad y buenas prácticas multi-lenguaje

### Linting y análisis estático ([lint])
- **flake8**: Linting de código Python
- **black**: Formateador de código
- **isort**: Ordenador de imports
- **mypy**: Comprobación de tipos
- **radon**: Complejidad ciclomática
- **pylint**: Análisis estático avanzado

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
sudo apt update && sudo apt install -y poppler-utils tesseract-ocr tesseract-ocr-spa && pip3 install --user -e .
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



## Despliegue en Azure Web Apps
La aplicación está configurada para desplegarse directamente en Azure Web Apps utilizando el moderno `pyproject.toml` y la estructura estándar de FastAPI. Azure puede generar automáticamente un `requirements.txt` durante el proceso de construcción.

## Configuración

La aplicación utiliza **configuración centralizada** con valores por defecto sensatos, lo que permite ejecutarla inmediatamente sin configuración adicional.

### Variables de Entorno (Opcionales)

La aplicación funciona **out-of-the-box** con valores por defecto. Solo necesitas configurar variables de entorno para casos específicos:

#### 🔧 **Variables Principales:**
```bash
# Servidor (opcional - valores por defecto funcionan bien)
PER_HOST=0.0.0.0        # Por defecto: 0.0.0.0
PER_PORT=8002           # Por defecto: 8002  
PER_DEBUG=false         # Por defecto: false

# Rutas (opcional - la estructura por defecto está optimizada)
PER_DATA_DIR=data                    # Por defecto: data
PER_EXAMS_DIR=data/exams            # Por defecto: data/exams
```

#### ⚙️ **Configuración por Entorno:**

**Desarrollo local:**
```bash
export PER_DEBUG=true
export PER_LOG_LEVEL=debug
make run
```

**Producción (Azure Web Apps):**
```bash
# Azure configura automáticamente:
# - PER_HOST=0.0.0.0
# - PER_PORT=8000
# - Variables específicas del entorno
```

#### 📋 **Lista Completa de Variables:**

Todas las variables están documentadas en `config/settings.py` con tipos, valores por defecto y descripciones. Principales grupos:

- **Servidor:** `PER_HOST`, `PER_PORT`, `PER_DEBUG`, `PER_RELOAD`, `PER_LOG_LEVEL`
- **API:** `PER_API_TITLE`, `PER_API_DESCRIPTION`, `PER_API_VERSION`
- **Rutas:** `PER_DATA_DIR`, `PER_EXAMS_DIR`, `PER_RAW_QUESTIONS_DIR`, etc.
- **Exámenes:** `PER_DEFAULT_NUM_QUESTIONS`, `PER_EXAM_TTL_HOURS`
- **Procesamiento:** `PER_OCR_CONFIDENCE_THRESHOLD`, `PER_PDF_DPI`

> **💡 Tip:** La aplicación está diseñada para funcionar sin configuración. Solo modifica variables si necesitas un comportamiento específico.