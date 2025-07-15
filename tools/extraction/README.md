# Extraction Tools - Herramientas de Extracción

Scripts especializados en extraer información de documentos PDF oficiales de exámenes PER.

## 📄 Scripts Disponibles

### `madrid_extract_questions.py`
# Extraction Tools - Herramientas de Extracción

Scripts especializados en extraer información de documentos PDF oficiales de exámenes PER.

## 📄 Scripts Disponibles

### `madrid_extract_questions.py`
**Propósito**: Extrae preguntas y estructura de exámenes desde PDFs oficiales de forma parametrizable.

**Características**:
- 🚢 **Extracción especializada PER**: Soporte específico para exámenes de Patrón de Embarcaciones de Recreo
- 🔍 **Reconocimiento inteligente**: Identifica automáticamente categorías y estructura del examen
- 📂 **Salida estructurada**: Genera archivos YAML organizados por las 11 categorías oficiales PER
- 🔧 **Recuperación automática**: Detecta y recupera preguntas que podrían haberse perdido en la extracción inicial
- ✅ **Validación robusta**: Verifica la integridad y completitud de las preguntas extraídas

#### Uso desde Línea de Comandos

```bash
python madrid_extract_questions.py --input-file RUTA_PDF --test-code NUMERO_TEST [--output-dir DIRECTORIO] [--verbose]
```

#### Parámetros Obligatorios

- `--input-file`: Archivo PDF que contiene las preguntas del examen
- `--test-code`: Número del test a extraer (`01`, `02`, `03`, `04`, `05`)

#### Parámetros Opcionales

- `--output-dir`: Directorio donde guardar el archivo YAML (default: `data/exams`)
- `--verbose`: Mostrar información detallada del procesamiento

#### Ejemplos de Uso

```bash
# Extraer Test 01 de Madrid 2025 abril
python madrid_extract_questions.py --input-file data/raw/questions/madrid-2025-abril.pdf --test-code 01

# Extraer Test 04 con información detallada y directorio personalizado
python madrid_extract_questions.py --input-file data/raw/questions/madrid-2025-abril.pdf --test-code 04 --output-dir mis_examenes --verbose

# Usar ruta absoluta al PDF
python madrid_extract_questions.py --input-file /workspaces/per-tests/data/raw/questions/madrid-2025-abril.pdf --test-code 02 --verbose

# Ver ayuda completa del script
python madrid_extract_questions.py --help
```

#### Categorías PER Soportadas

El script organiza automáticamente las preguntas en las 11 categorías oficiales del PER:

1. **Nomenclatura náutica** - Terminología básica de embarcaciones
2. **Elementos de amarre y fondeo** - Cabos, nudos, anclas y maniobras de puerto  
3. **Seguridad** - Equipos de seguridad y supervivencia
4. **Legislación** - Normativa y regulaciones náuticas
5. **Balizamiento** - Señalización marítima y ayudas a la navegación
6. **Reglamento (RIPA)** - Reglas Internacionales para Prevenir Abordajes
7. **Maniobra y navegación** - Técnicas de gobierno y maniobra
8. **Emergencias en la mar** - Procedimientos de emergencia y rescate
9. **Meteorología** - Tiempo, viento y condiciones meteorológicas
10. **Teoría de la navegación** - Conceptos fundamentales de navegación
11. **Carta de navegación** - Interpretación y uso de cartas náuticas

#### Nomenclatura de Archivos

**Archivos de Entrada (PDFs)**:
- Formato esperado: `{comunidad}-{año}-{convocatoria}.pdf`
- Ejemplos: `madrid-2025-abril.pdf`, `valencia-2024-junio.pdf`

**Archivos de Salida (YAML)**:
- Formato generado: `per-{test}-{comunidad}-{año}-{convocatoria}.yaml`
- Ejemplos: `per-test01-madrid-2025-abril.yaml`, `per-test04-madrid-2025-abril.yaml`

**Salida**: Archivos YAML estructurados en el directorio especificado con preguntas organizadas por categorías.
- Patrón: `{comunidad}-{año}-{convocatoria}.pdf`
- Ejemplos: `madrid-2025-abril.pdf`, `valencia-2024-junio.pdf`

**Archivos de Salida (YAML)**:
- Patrón: `per-{test}-{comunidad}-{año}-{convocatoria}.yaml`
- Ejemplos: `per-test01-madrid-2025-abril.yaml`, `per-test03-valencia-2024-junio.yaml`

**Salida**: Archivos YAML en `data/exams/` con preguntas estructuradas por categorías.

---

### `madrid_extract_answers_v2.py`
**Propósito**: Extrae respuestas oficiales de PDFs usando OCR (Reconocimiento Óptico de Caracteres).

**Características**:
- 🤖 **OCR avanzado**: Reconocimiento óptico con preprocesamiento de imágenes
- 🎯 **Filtros específicos**: Extrae solo el tipo de examen y modelo deseado
- ✅ **Detección automática**: Identifica respuestas múltiples y anuladas
- 🔍 **Validación de consistencia**: Verifica la coherencia de las respuestas
- 📋 **Soporte múltiples formatos**: Maneja diferentes layouts de hojas de respuestas

#### Parámetros de Línea de Comandos

- `--input-file`: Archivo PDF de respuestas oficiales (obligatorio)
- `--output-dir`: Directorio de salida para archivos JSON (default: extracted-answers)
- `--verbose`: Mostrar información detallada del procesamiento

#### Ejemplos de Uso

```bash
# Extraer respuestas con archivo específico
python madrid_extract_answers_v2.py --input-file madrid-2025-abril-respuestas.pdf

# Extraer con información detallada y directorio personalizado
python madrid_extract_answers_v2.py --input-file respuestas.pdf --output-dir mi_directorio --verbose

# Especificar archivo PDF completo
python madrid_extract_answers_v2.py --input-file "/ruta/madrid-2024-noviembre-respuestas.pdf" --verbose
```

**Salida**: Archivos JSON en `extracted-answers/` con respuestas extraídas.

## 🔄 Flujo de Trabajo Completo

### Extracción de Preguntas de Madrid 2025 abril:
```bash
cd /workspaces/per-tests/tools/extraction

# Extraer Test 01
python madrid_extract_questions.py --input-file data/raw/questions/madrid-2025-abril.pdf --test-code 01

# Extraer Test 02  
python madrid_extract_questions.py --input-file data/raw/questions/madrid-2025-abril.pdf --test-code 02

# Extraer Test 03
python madrid_extract_questions.py --input-file data/raw/questions/madrid-2025-abril.pdf --test-code 03

# Extraer Test 04
python madrid_extract_questions.py --input-file data/raw/questions/madrid-2025-abril.pdf --test-code 04

# Extraer Test 05
python madrid_extract_questions.py --input-file data/raw/questions/madrid-2025-abril.pdf --test-code 05
```

### Flujo Completo (Preguntas + Respuestas):
```bash
cd /workspaces/per-tests/tools/extraction

# 1. Extraer preguntas del test deseado
python madrid_extract_questions.py --input-file data/raw/questions/madrid-2025-abril.pdf --test-code 01

# 2. Extraer respuestas del mismo test
python madrid_extract_answers_v2.py --exam-type PER --test-model TEST01

# 3. Verificar archivos generados
ls -la ../../data/exams/per-test01-madrid-2025-abril.yaml
ls -la extracted_answers/
```

### Para otros archivos PDF:
```bash
# Usar rutas absolutas para PDFs en otras ubicaciones
python madrid_extract_questions.py --input-file /ruta/completa/al/pdf/examen.pdf --test-code 02

# Especificar directorio de salida personalizado
python madrid_extract_questions.py --input-file data/raw/questions/madrid-2025-abril.pdf --test-code 03 --output-dir mis_examenes
```

### Flujo Completo:
1. **Preparar PDFs**: Colocar PDFs originales en `data/raw/questions/` y `data/raw/answers/`
2. **Extraer preguntas**: Ejecutar `madrid_extract_questions.py` con parámetros apropiados
3. **Extraer respuestas**: Ejecutar `madrid_extract_answers_v2.py` con PDF correcto
4. **Procesar datos**: Continuar con herramientas de `processing/`

## 🛠️ Dependencias del Sistema

### Dependencias Automáticas (DevContainer)
El devcontainer instala automáticamente:
- `poppler-utils`: Para conversión PDF a imágenes
- `tesseract-ocr`: Motor de OCR
- `tesseract-ocr-spa`: Soporte para español

### Dependencias de Python
```bash
pip install -r requirements.txt
```

Librerías específicas:
- PyMuPDF (fitz)
- pdf2image 
- pytesseract
- Pillow (PIL)
- OpenCV (cv2)
- PyYAML

### Verificación de Instalación
```bash
# Verificar poppler
pdfinfo --version

# Verificar tesseract
tesseract --version

# Verificar idiomas disponibles
tesseract --list-langs
```

## 🔧 Solución de Problemas

### Errores Comunes del Extractor de Preguntas:

**`No se encuentra el archivo PDF`**:
```bash
# Verificar que el archivo existe
ls -la data/raw/questions/madrid-2025-abril.pdf

# Usar ruta absoluta si es necesario
python madrid_extract_questions.py --input-file /workspaces/per-tests/data/raw/questions/madrid-2025-abril.pdf --test-code 01
```

**`No se encontró el patrón de inicio del examen`**:
- Verifica que el PDF contiene el test especificado (01, 02, 03, 04, 05)
- Algunos PDFs pueden tener variaciones en el formato del título
- Revisa el contenido del PDF manualmente para confirmar la presencia del examen

**`Preguntas faltantes detectadas`**:
- El script intentará recuperar automáticamente las preguntas faltantes
- Esto es normal y suele resolverse satisfactoriamente
- Si persisten faltantes, puede indicar un problema en el formato del PDF

**Error de permisos de escritura**:
```bash
# Crear directorio si no existe
mkdir -p data/exams

# Verificar permisos
ls -la data/
```

### Errores Comunes del Extractor de Respuestas:

**`PDFInfoNotInstalledError`**:
```bash
sudo apt install poppler-utils
```

**`tesseract is not installed`**:
```bash
sudo apt install tesseract-ocr tesseract-ocr-spa
```

### Verificación de Instalación de Dependencias:
```bash
# Verificar poppler
pdfinfo --version

# Verificar tesseract
tesseract --version

# Verificar idiomas disponibles
tesseract --list-langs
```

## 📋 Integración con Otros Scripts

Los archivos generados son compatibles con:
- `madrid_apply_answers.py`: Para aplicar respuestas extraídas a los archivos YAML
- Aplicación web: Para visualizar exámenes
- Scripts de procesamiento: Para análisis adicional

## 💡 Consejos y Mejores Prácticas

### Para el Extractor de Preguntas:
- Usar siempre rutas absolutas cuando trabajas con PDFs en diferentes directorios
- Verificar la integridad del PDF antes de la extracción
- Revisar el resumen de extracción para confirmar que se obtuvieron todas las preguntas
- Los archivos YAML generados mantienen el orden secuencial de las preguntas (1-45)

### Para el Extractor de Respuestas:
- Los filtros de `madrid_extract_answers.py` permiten extraer solo las respuestas necesarias
- El OCR funciona mejor con PDFs de alta resolución (300+ DPI)  
- Revisar siempre los archivos de salida para validar la extracción

### Flujo de Trabajo Recomendado:
1. Colocar PDFs originales en `data/raw/questions/` y `data/raw/answers/`
2. Extraer preguntas usando `madrid_extract_questions.py`
3. Extraer respuestas usando `madrid_extract_answers.py`
4. Verificar archivos generados antes de continuar con el procesamiento
5. Usar herramientas de `processing/` para combinar y analizar los datos
