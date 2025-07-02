# Extractor Parametrizable de Exámenes PER

El script `madrid_extract_questions.py` ahora es completamente parametrizable y puede extraer exámenes de diferentes comunidades, años y convocatorias.

## Características Nuevas

### ✨ Parámetros de Línea de Comandos

- `--community`: Comunidad autónoma (ej: Madrid, Valencia, Barcelona)
- `--year`: Año del examen (ej: 2024, 2025)
- `--call`: Convocatoria (ej: abril, junio, septiembre, noviembre)
- `--test`: Código del test (ej: test01, test02, test03)
- `--total-questions`: Número total de preguntas esperadas (por defecto: 45)

### 📁 Opciones de Archivos

- `--pdf-file`: Especificar archivo PDF completo
- `--pdf-pattern`: Patrón personalizado para buscar PDF
- `--output-dir`: Directorio de salida personalizado
- `--output-file`: Nombre de archivo de salida específico

### 🔍 Búsqueda Inteligente de PDFs

El script puede:
- Buscar automáticamente PDFs basándose en los parámetros
- Usar patrones flexibles con wildcards
- Mostrar archivos disponibles cuando no encuentra coincidencias

## Ejemplos de Uso

### Uso Básico (por defecto: Madrid 2025 abril test01)
```bash
python madrid_extract_questions.py
```

### Extraer Test Específico
```bash
# Extraer test03 de Madrid 2025 abril
python madrid_extract_questions.py --test test03
```

### Extraer de Diferentes Comunidades/Años
```bash
# Valencia 2024 junio
python madrid_extract_questions.py --community Valencia --year 2024 --call junio

# Barcelona 2023 extraordinaria
python madrid_extract_questions.py --community Barcelona --year 2023 --call extraordinaria
```

### Usar Archivo PDF Específico
```bash
# Especificar archivo completo
python madrid_extract_questions.py --pdf-file "/ruta/completa/al/archivo.pdf"

# Usar patrón personalizado
python madrid_extract_questions.py --pdf-pattern "valencia-2024-junio"
```

### Personalizar Salida
```bash
# Directorio de salida personalizado
python madrid_extract_questions.py --output-dir "/mi/directorio/salida"

# Archivo de salida específico
python madrid_extract_questions.py --output-file "/ruta/completa/mi-examen.yaml"
```

## Nomenclatura de Archivos

### Archivos de Entrada (PDFs)
El script busca PDFs con el patrón: `{comunidad}-{año}-{convocatoria}.pdf`

Ejemplos:
- `madrid-2025-abril.pdf`
- `valencia-2024-junio.pdf`
- `barcelona-2023-extraordinaria.pdf`

### Archivos de Salida (YAML)
Genera archivos con el patrón: `per-{test}-{comunidad}-{año}-{convocatoria}.yaml`

Ejemplos:
- `per-test01-madrid-2025-abril.yaml`
- `per-test03-valencia-2024-junio.yaml`
- `per-test02-barcelona-2023-extraordinaria.yaml`

## Manejo de Errores

El script incluye manejo robusto de errores:

- ✅ Muestra archivos PDF disponibles cuando no encuentra coincidencias
- ✅ Proporciona sugerencias de uso con `--pdf-pattern` y `--pdf-file`
- ✅ Valida que los archivos especificados existan
- ✅ Busca con patrones flexibles usando wildcards

## Integración con Otros Scripts

Los archivos YAML generados son compatibles con:
- `madrid_extract_answers.py` para extraer respuestas
- `madrid_merge_exam.py` para combinar preguntas y respuestas
- La aplicación web para mostrar exámenes

## Función Helper: create_per_pattern()

Para crear nuevos patrones de examen fácilmente:

```python
from madrid_extract_questions import create_per_pattern

# Crear patrón para Valencia 2024 junio
pattern = create_per_pattern("Valencia", 2024, "Junio", "Test02")

# Usar el patrón con el extractor
extractor = ParametricExamExtractor()
exam_data = extractor.extract_exam("valencia-2024-junio.pdf", pattern)
```

## Requisitos

- Python 3.7+
- PyMuPDF (fitz)
- PyYAML
- Estructura de directorios configurada en `config/settings.py`

## Próximos Pasos

Después de extraer las preguntas, recuerda:

1. **Extraer respuestas**: Usar `madrid_extract_answers.py`
2. **Combinar datos**: Usar `madrid_merge_exam.py` si es necesario
3. **Verificar resultados**: Revisar el archivo YAML generado

El script te proporciona comandos específicos al final de la ejecución.
