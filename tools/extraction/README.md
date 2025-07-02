# Extraction Tools - Herramientas de Extracción

Scripts especializados en extraer información de documentos PDF oficiales.

## 📄 Scripts Disponibles

### `parametric_exam_extractor.py`
**Propósito**: Extrae preguntas y estructura de exámenes desde PDFs oficiales.

**Características**:
- Procesamiento parametrizado para diferentes tipos de examen
- Extracción automática de categorías y preguntas
- Generación de archivos YAML estructurados
- Soporte para múltiples formatos de examen

**Uso**:
```bash
cd /workspaces/per-tests
python tools/extraction/parametric_exam_extractor.py
```

**Salida**: Archivos YAML en `data/exams/` con preguntas estructuradas por categorías.

---

### `madrid_extract_answers.py`
**Propósito**: Extrae respuestas oficiales de PDFs usando OCR (Reconocimiento Óptico de Caracteres).

**Características**:
- OCR avanzado con preprocesamiento de imágenes
- Detección automática de respuestas múltiples
- Soporte para diferentes formatos de hojas de respuestas
- Validación de consistencia de respuestas
- Manejo de respuestas anuladas

**Uso**:
```bash
cd /workspaces/per-tests
python tools/extraction/madrid_extract_answers.py [--pdf-path RUTA_PDF] [--output-dir DIRECTORIO_SALIDA]
```

**Parámetros**:
- `--pdf-path`: Ruta al PDF de respuestas (default: ../../data/raw/answers/madrid-2025-resp.pdf)
- `--output-dir`: Directorio de salida (default: ../../extracted_answers)

**Salida**: Archivos JSON en `extracted_answers/` con respuestas extraídas.

## 🔄 Flujo de Trabajo

1. **Preparar PDFs**: Colocar PDFs originales en `data/raw/questions/` y `data/raw/answers/`
2. **Extraer preguntas**: Ejecutar `parametric_exam_extractor.py`
3. **Extraer respuestas**: Ejecutar `madrid_extract_answers.py`
4. **Procesar datos**: Continuar con herramientas de `processing/`

## 🛠️ Dependencias

Estas herramientas requieren las dependencias completas del proyecto:
```bash
pip install -r requirements.txt
```

Dependencias específicas:
- PyMuPDF (fitz)
- pdf2image
- pytesseract 
- Pillow (PIL)
- OpenCV (cv2)

## 📋 Notas Técnicas

- Los scripts usan rutas relativas desde la raíz del proyecto
- Requieren Tesseract OCR instalado en el sistema
- Optimizados para resoluciones altas (300+ DPI)
- Incluyen validación automática de resultados
