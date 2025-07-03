# Extraction Tools - Herramientas de Extracción

Scripts especializados en extraer información de documentos PDF oficiales de exámenes PER.

## 📄 Scripts Disponibles

### `madrid_extract_questions.py`
**Propósito**: Extrae preguntas y estructura de exámenes desde PDFs oficiales. **Ahora completamente parametrizable**.

**Características**:
- ✨ **Extracción parametrizable**: Soporte para diferentes comunidades, años y convocatorias
- 🔍 **Búsqueda inteligente de PDFs**: Encuentra automáticamente archivos basándose en parámetros
- 📂 **Múltiples opciones de salida**: Personaliza directorios y nombres de archivo
- 🏷️ **Categorización automática**: Organiza preguntas por categorías oficiales del PER
- 🔧 **Manejo robusto de errores**: Suggestions y validaciones útiles

#### Parámetros de Línea de Comandos

- `--community`: Comunidad autónoma (ej: Madrid, Valencia, Barcelona)
- `--year`: Año del examen (ej: 2024, 2025)
- `--call`: Convocatoria (ej: abril, junio, septiembre, noviembre)
- `--test`: Código del test (ej: test01, test02, test03)
- `--total-questions`: Número total de preguntas esperadas (por defecto: 45)
- `--pdf-file`: Especificar archivo PDF completo
- `--pdf-pattern`: Patrón personalizado para buscar PDF
- `--output-dir`: Directorio de salida personalizado
- `--output-file`: Nombre de archivo de salida específico

#### Ejemplos de Uso

```bash
# Uso básico (por defecto: Madrid 2025 abril test01)
python madrid_extract_questions.py

# Extraer test específico
python madrid_extract_questions.py --test test03

# Extraer de diferentes comunidades/años
python madrid_extract_questions.py --community Valencia --year 2024 --call junio

# Usar archivo PDF específico
python madrid_extract_questions.py --pdf-file "/ruta/completa/al/archivo.pdf"

# Con archivo de salida personalizado
python madrid_extract_questions.py --output-file "mi-examen.yaml"
```

#### Nomenclatura de Archivos

**Archivos de Entrada (PDFs)**:
- Patrón: `{comunidad}-{año}-{convocatoria}.pdf`
- Ejemplos: `madrid-2025-abril.pdf`, `valencia-2024-junio.pdf`

**Archivos de Salida (YAML)**:
- Patrón: `per-{test}-{comunidad}-{año}-{convocatoria}.yaml`
- Ejemplos: `per-test01-madrid-2025-abril.yaml`, `per-test03-valencia-2024-junio.yaml`

**Salida**: Archivos YAML en `data/exams/` con preguntas estructuradas por categorías.

---

### `madrid_extract_answers.py`
**Propósito**: Extrae respuestas oficiales de PDFs usando OCR (Reconocimiento Óptico de Caracteres).

**Características**:
- 🤖 **OCR avanzado**: Reconocimiento óptico con preprocesamiento de imágenes
- 🎯 **Filtros específicos**: Extrae solo el tipo de examen y modelo deseado
- ✅ **Detección automática**: Identifica respuestas múltiples y anuladas
- 🔍 **Validación de consistencia**: Verifica la coherencia de las respuestas
- 📋 **Soporte múltiples formatos**: Maneja diferentes layouts de hojas de respuestas

#### Parámetros de Línea de Comandos

- `--exam-type`: Tipo de examen (PER, PATRON_YATE, CAPITAN_YATE, LICENCIA_NAVEGACION)
- `--test-model`: Modelo específico (TEST01, TEST02, TEST03, etc.)
- `--pdf-path`: Ruta al archivo PDF de respuestas
- `--output-dir`: Directorio de salida para archivos JSON

#### Ejemplos de Uso

```bash
# Extraer todas las respuestas
python madrid_extract_answers.py

# Extraer respuestas de un tipo específico
python madrid_extract_answers.py --exam-type PER

# Extraer respuestas de un modelo específico
python madrid_extract_answers.py --exam-type PER --test-model TEST01

# Especificar archivo PDF personalizado (para otros años/convocatorias)
python madrid_extract_answers.py --exam-type PER --test-model TEST01 --pdf-path "/ruta/madrid-2024-noviembre.pdf"
```

**Salida**: Archivos JSON en `extracted_answers/` con respuestas extraídas.

## 🔄 Flujo de Trabajo Completo

### Para Madrid 2025 abril (por defecto):
```bash
cd /workspaces/per-tests/tools/extraction

# 1. Extraer preguntas (test01)
python madrid_extract_questions.py

# 2. Extraer respuestas (test01)
python madrid_extract_answers.py --exam-type PER --test-model TEST01
```

### Para otros años/convocatorias:
```bash
cd /workspaces/per-tests/tools/extraction

# 1. Extraer preguntas de Madrid 2024 noviembre test01
python madrid_extract_questions.py --year 2024 --call noviembre --test test01

# 2. Extraer respuestas del mismo examen
python madrid_extract_answers.py --exam-type PER --test-model TEST01 --pdf-path "/workspaces/per-tests/data/raw/answers/madrid-2024-noviembre.pdf"
```

### Flujo Completo:
1. **Preparar PDFs**: Colocar PDFs originales en `data/raw/questions/` y `data/raw/answers/`
2. **Extraer preguntas**: Ejecutar `madrid_extract_questions.py` con parámetros apropiados
3. **Extraer respuestas**: Ejecutar `madrid_extract_answers.py` con PDF correcto
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

### Errores Comunes:

**`PDFInfoNotInstalledError`**:
```bash
sudo apt install poppler-utils
```

**`tesseract is not installed`**:
```bash
sudo apt install tesseract-ocr tesseract-ocr-spa
```

**No encuentra PDF**:
- Verifica la nomenclatura: `{comunidad}-{año}-{convocatoria}.pdf`
- Usa `--pdf-file` para rutas específicas
- Usa `--pdf-pattern` para patrones personalizados

**Año/convocatoria incorrectos**:
- Los metadatos del archivo YAML reflejan los parámetros usados
- Para Madrid 2024 noviembre, usa: `--year 2024 --call noviembre`

## 📋 Integración con Otros Scripts

Los archivos generados son compatibles con:
- `madrid_merge_exam.py`: Para combinar preguntas y respuestas
- Aplicación web: Para visualizar exámenes
- Scripts de procesamiento: Para análisis adicional

## 💡 Consejos

- Usar nombres descriptivos para archivos de salida cuando trabajes con múltiples convocatorias
- Los filtros de `madrid_extract_answers.py` permiten extraer solo las respuestas necesarias
- El OCR funciona mejor con PDFs de alta resolución (300+ DPI)
- Revisar siempre los archivos de salida para validar la extracción
