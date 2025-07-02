# Utility Tools - Herramientas de Análisis y Utilidades

Herramientas de desarrollo, análisis y utilidades compartidas.

## 📄 Scripts Disponibles

### `pdf_analyzer.py`
**Propósito**: Herramienta de análisis para entender la estructura de documentos PDF antes de procesarlos.

**Características**:
- Análisis detallado de estructura de páginas
- Extracción de texto con coordenadas
- Análisis de fuentes y estilos
- Detección de elementos gráficos
- Generación de reportes de análisis
- Útil para debugging y desarrollo de nuevos extractores

**Uso**:
```bash
cd /workspaces/per-tests
python tools/utils/pdf_analyzer.py [--pdf-path RUTA_PDF] [--output-dir DIRECTORIO_SALIDA]
```

**Parámetros**:
- `--pdf-path`: Ruta al PDF a analizar
- `--output-dir`: Directorio donde guardar el análisis
- `--detailed`: Análisis detallado (opcional)
- `--pages`: Páginas específicas a analizar (opcional)

**Salida**: 
- Reporte de análisis en formato texto
- Extracción de texto por páginas
- Información de metadatos del PDF
- Mapeo de elementos estructurales

## 🔍 Casos de Uso

### Desarrollo de Nuevos Extractores
Antes de crear un extractor para un nuevo tipo de examen:

1. **Análisis inicial**:
   ```bash
   python tools/utils/pdf_analyzer.py --pdf-path nuevo_examen.pdf --detailed
   ```

2. **Revisar estructura**: Examinar el reporte generado para entender:
   - Distribución de texto en las páginas
   - Patrones de preguntas y respuestas
   - Elementos repetitivos
   - Formato de numeración

3. **Desarrollar extractor**: Usar la información para crear regex y lógica de extracción

### Debugging de Extractores Existentes
Cuando un extractor no funciona correctamente:

1. **Comparar estructura**: Analizar si el PDF tiene formato diferente al esperado
2. **Identificar cambios**: Detectar modificaciones en el formato oficial
3. **Ajustar parámetros**: Modificar el extractor basándose en el análisis

## 📊 Ejemplo de Salida

```
=== ANÁLISIS DE PDF ===
Archivo: examen_per_madrid_2025.pdf
Páginas: 12
Tamaño: A4 (595.32 x 841.89 pts)

=== PÁGINA 1 ===
Elementos de texto: 45
Fuentes detectadas: 
  - Times-Roman: 32 elementos
  - Times-Bold: 13 elementos

Patrones detectados:
  - Numeración de preguntas: "1.", "2.", "3."
  - Opciones: "a)", "b)", "c)", "d)"
  - Categorías: Detectadas 11 secciones

=== RECOMENDACIONES ===
- Usar regex: r"(\d+)\.\s*(.*?)(?=\d+\.|$)"
- Extraer opciones con: r"([a-d])\)\s*(.*?)(?=[a-d]\)|$)"
- Categorías por página: Sí
```

## 🛠️ Funciones Auxiliares

Este directorio también puede contener utilidades compartidas entre diferentes scripts:

- **Funciones de validación**: Verificación de formatos
- **Helpers de procesamiento**: Funciones comunes de manipulación de datos
- **Constantes compartidas**: Patrones regex, configuraciones
- **Utilidades de archivo**: Manejo de rutas y backups

## 📋 Notas de Desarrollo

- Útil para el desarrollo de nuevos extractores
- No modifica archivos originales, solo analiza
- Generar reportes antes de procesar PDFs desconocidos
- Documentar hallazgos para futura referencia
