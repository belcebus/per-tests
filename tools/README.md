# Tools - Scripts de Procesamiento de PDFs

Este directorio contiene los scripts esenciales para procesar los PDFs oficiales de exámenes y convertirlos a archivos YAML que utiliza la aplicación.

## Scripts Disponibles

### 🔧 Scripts de Procesamiento Principal

- **`parametric_exam_extractor.py`** - Extractor parametrizable de exámenes desde PDFs. Script principal para extraer exámenes específicos usando patrones de título y subtítulo.

- **`pdf_to_yaml.py`** - Procesador que convierte PDFs de exámenes a archivos YAML con la estructura diseñada para la aplicación.

- **`complete_pdf_processor.py`** - Procesador completo que extrae todos los tipos de examen y códigos de test de un PDF.

- **`clean_per_processor.py`** - Procesador específico para exámenes de PER, clasificando las preguntas por categorías oficiales.

- **`process_official_answers.py`** - Procesador de respuestas oficiales desde el PDF de respuestas.

### 🔍 Scripts de Análisis

- **`pdf_analyzer.py`** - Analizador de estructura de PDFs. Útil para analizar nuevos PDFs antes de procesarlos.

## Uso

Estos scripts están diseñados para ser ejecutados desde la línea de comandos cuando sea necesario procesar nuevos PDFs oficiales o actualizar el contenido de las preguntas.

```bash
# Ejemplo de uso del extractor parametrizable
python tools/parametric_exam_extractor.py

# Ejemplo de análisis de un PDF
python tools/pdf_analyzer.py
```

## Archivos de Entrada

Los scripts esperan encontrar los PDFs oficiales en el directorio `pdfs/` del proyecto.

## Archivos de Salida

Los archivos YAML generados se guardan en el directorio `data/` del proyecto, donde la aplicación los lee para generar los exámenes.
