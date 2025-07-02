# Tools - Scripts de Procesamiento de PDFs

Este directorio contiene los scripts esenciales para procesar los PDFs oficiales de exámenes y convertirlos a archivos YAML que utiliza la aplicación.

## 📁 Estructura Organizada

### 🔍 `extraction/` - Extracción de Datos
Scripts especializados en extraer información de PDFs:
- **`madrid_extract_questions.py`** - Extrae preguntas y estructura de exámenes de Madrid
- **`madrid_extract_answers.py`** - Extrae respuestas oficiales de Madrid usando OCR

### ⚙️ `processing/` - Procesamiento de Datos  
Scripts para procesar y transformar datos extraídos:
- **`madrid_merge_exam.py`** - Aplica respuestas extraídas a archivos YAML

### 🛠️ `utils/` - Utilidades y Análisis
Herramientas de desarrollo y análisis:
- **`pdf_analyzer.py`** - Análisis de estructura de PDFs para desarrollo

## 🚀 Flujo de Procesamiento End-to-End

### Paso 1: Extracción de Preguntas
**`extraction/madrid_extract_questions.py`** - Extractor principal que procesa PDFs de exámenes de Madrid y genera archivos YAML con las preguntas estructuradas por categorías.

### Paso 2: Extracción de Respuestas OCR  
**`extraction/madrid_extract_answers.py`** - Extrae respuestas oficiales de PDFs de Madrid usando OCR (reconocimiento óptico de caracteres). Procesa múltiples tipos de examen y genera archivos JSON con las respuestas.

### Paso 3: Aplicación de Respuestas
**`processing/madrid_merge_exam.py`** - Aplica las respuestas extraídas por OCR al archivo YAML de preguntas, generando un backup automático del archivo original.

## � Scripts de Desarrollo

### Análisis de PDFs
**`utils/pdf_analyzer.py`** - Herramienta de análisis para entender la estructura de nuevos PDFs antes de procesarlos. Útil para debugging y desarrollo.

## 📝 Uso Típico

```bash
# 1. Extraer preguntas del PDF de examen
python tools/extraction/madrid_extract_questions.py

# 2. Extraer respuestas oficiales usando OCR
python tools/extraction/madrid_extract_answers.py

# 3. Aplicar respuestas al archivo YAML
python tools/processing/madrid_merge_exam.py

# 4. (Opcional) Analizar nuevo PDF antes de procesarlo
python tools/utils/pdf_analyzer.py
```

## 📁 Estructura de Archivos

### Archivos de Entrada
- `pdfs/` - PDFs oficiales de exámenes y respuestas

### Archivos de Salida
- `data/` - Archivos YAML finales para la aplicación
- `extracted_answers/` - Respuestas extraídas por OCR en formato JSON

## ✅ Proceso Verificado

Este flujo ha sido probado exitosamente con:
- **Examen**: PER Madrid 2025 Test 01 (45 preguntas)
- **Precisión**: 100% verificada contra archivo de referencia
- **Funcionalidad**: Completamente integrado en la aplicación web
