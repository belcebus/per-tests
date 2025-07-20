# Tools - Scripts de Procesamiento de PDFs

Este directorio contiene los scripts esenciales para procesar los PDFs oficiales de exámenes y convertirlos a archivos YAML que utiliza la aplicación.

## 📁 Estructura Organizada

### 🔍 `extraction/` - Extracción de Datos
Scripts especializados en extraer información de PDFs:
- **`madrid_extract_questions.py`** - Extrae preguntas y estructura de exámenes de Madrid
- **`madrid_extract_answers_v2.py`** - Extrae respuestas oficiales de Madrid usando OCR

### ⚙️ `processing/` - Procesamiento de Datos  
Scripts para procesar y transformar datos extraídos:
- **`madrid_apply_answers.py`** - Aplica respuestas extraídas a archivos YAML

### 🔧 `utils/` - Herramientas de Utilidad
Scripts de análisis y verificación para desarrollo y control de calidad:
- **`check_exam_consistency.py`** - Verifica la consistencia de distribución de preguntas por categorías

---

# 📄 Documentación Detallada de Scripts

## 🔍 EXTRACTION - Herramientas de Extracción

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
- `--test-code`: Número del test a extraer (`01`, `02`, `03`, `04`, `05`, `06`)

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

---

### `madrid_extract_answers_v2.py`
**Propósito**: Extrae respuestas oficiales de PDFs usando OCR (Reconocimiento Óptico de Caracteres).

**Características**:
- 🤖 **OCR avanzado**: Reconocimiento óptico con preprocesamiento de imágenes
- 🎯 **Filtros específicos**: Extrae solo el tipo de examen y modelo deseado
- ✅ **Detección automática**: Identifica respuestas múltiples y anuladas
- 📋 **Múltiples formatos**: Soporte para diferentes layouts de PDFs oficiales

#### Uso desde Línea de Comandos

```bash
python madrid_extract_answers_v2.py --input-file ARCHIVO_PDF [--output-dir DIRECTORIO] [--verbose]
```

#### Parámetros Obligatorios

- `--input-file`: Archivo PDF de respuestas oficiales

#### Parámetros Opcionales

- `--output-dir`: Directorio de salida (default: `extracted-answers/`)
- `--verbose`: Mostrar información detallada del procesamiento

#### Ejemplos de Uso

```bash
# Extraer respuestas del PDF de Madrid 2025 abril
python madrid_extract_answers_v2.py --input-file "data/raw/answers/madrid/2025/madrid-2025-abril.pdf"

# Extraer respuestas de un PDF específico con directorio personalizado
python madrid_extract_answers_v2.py --input-file "data/raw/answers/madrid/2024/madrid-2024-junio.pdf" --output-dir "resultados_ocr"

# Extraer respuestas con información detallada
python madrid_extract_answers_v2.py --input-file "data/raw/answers/madrid/2023/madrid-2023-noviembre.pdf" --verbose
```

**Nota**: El script detecta automáticamente el tipo de examen y modelo desde el contenido del PDF usando OCR.

---

## ⚙️ PROCESSING - Herramientas de Procesamiento

### `madrid_apply_answers.py`
**Propósito**: Aplica respuestas oficiales extraídas por OCR a archivos YAML de preguntas.

**Características**:
- 🔄 **Aplicación automática**: Combina respuestas JSON con preguntas YAML
- 🛡️ **Backup automático**: Genera respaldos antes de modificar archivos
- ✅ **Validación de consistencia**: Verifica correspondencia entre preguntas y respuestas
- 🔍 **Manejo de casos especiales**: Detecta y procesa respuestas anuladas
- 📊 **Reportes detallados**: Estadísticas de aplicación y posibles inconsistencias

#### Uso desde Línea de Comandos

```bash
python madrid_apply_answers.py [--input-file ARCHIVO_JSON] [--target-file ARCHIVO_YAML] [--output-dir DIRECTORIO] [--verbose]
```

#### Parámetros Opcionales

- `--input-file`: Archivo JSON con respuestas extraídas (auto-detecta si no se especifica)
- `--target-file`: Archivo YAML del examen a actualizar (auto-detecta si no se especifica)
- `--output-dir`: Directorio de salida (default: mismo directorio del archivo objetivo)
- `--verbose`: Mostrar información detallada del procesamiento

#### Ejemplos de Uso

```bash
# Aplicar respuestas usando auto-detección (recomendado)
python tools/processing/madrid_apply_answers.py --verbose

# Especificar archivos específicos
python tools/processing/madrid_apply_answers.py --input-file per-test01-respuestas.json --target-file per-test01-examen.yaml

# Usar directorio de salida personalizado
python tools/processing/madrid_apply_answers.py --output-dir mis_examenes_procesados --verbose
```

#### Formato de Entrada

**Archivo JSON de Respuestas**:
```json
{
  "1": "a",
  "2": "b", 
  "3": "ANULADA",
  "4": "c"
}
```

**Archivo YAML de Preguntas**:
```yaml
exam_info:
  title: "EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO"
categories:
  "1":
    name: "Nomenclatura náutica"
    questions:
      - id: 1
        question: "Pregunta de ejemplo"
        options:
          a: "Opción A"
          b: "Opción B"
        correct_answer: "a"  # Se actualiza automáticamente
```

#### Seguridad de Datos

- **Backups automáticos**: Se crea una copia de seguridad en `data/backups/` antes de cualquier modificación
- **Validación**: Verificación de integridad antes y después del procesamiento  
- **Logs detallados**: Registro completo de todas las operaciones realizadas

---

## 🔧 UTILS - Herramientas de Utilidad

### `check_exam_consistency.py`
**Propósito**: Verifica que todos los exámenes YAML sigan la distribución oficial de categorías definida en `settings.py`.

**Funcionalidades**:
- ✅ **Análisis Completo**: Revisa todos los archivos YAML en `data/exams/`
- 📊 **Distribución de Referencia**: Compara contra la configuración oficial
- 🔍 **Detección de Problemas**: Identifica exámenes con clasificación incorrecta
- 📈 **Estadísticas**: Calcula tasa de consistencia global
- 📋 **Reportes Detallados**: Muestra diferencias por categoría y examen

#### Distribución Oficial PER (45 preguntas total)

```
 1: Nomenclatura náutica        (4 preguntas)
 2: Elementos de amarre y fondeo (2 preguntas)
 3: Seguridad                   (4 preguntas)
 4: Legislación                 (2 preguntas)
 5: Balizamiento                (5 preguntas)
 6: Reglamento (RIPA)           (10 preguntas) ← Categoría principal
 7: Maniobra y navegación       (2 preguntas)
 8: Emergencias en la mar       (3 preguntas)
 9: Meteorología                (4 preguntas)
10: Teoría de la navegación     (5 preguntas)
11: Carta de navegación         (4 preguntas)
```

#### Uso desde Línea de Comandos

```bash
# Ejecutar análisis completo
python tools/utils/check_exam_consistency.py

# Con entorno virtual
source venv/bin/activate
python tools/utils/check_exam_consistency.py
```

#### Ejemplo de Salida

```
🔍 Verificando consistencia de exámenes PER...
📋 Distribución oficial (settings.py): 45 preguntas total
🔍 Encontrados 49 archivos de exámenes

📊 RESUMEN FINAL:
✅ Exámenes consistentes: 45
❌ Exámenes inconsistentes: 4  
💥 Exámenes con errores: 0
📈 TASA DE CONSISTENCIA: 91.8%
```

#### Interpretación de Resultados

- **✅ Consistentes**: Exámenes que cumplen exactamente la distribución oficial
- **❌ Inconsistentes**: Exámenes con diferencias en la distribución por categorías
- **💥 Con errores**: Archivos que no se pudieron cargar o tienen estructura incorrecta

#### Casos de Uso

**Control de Calidad Pre-Extracción**:
```bash
# Verificar estado actual antes de agregar nuevos exámenes
python tools/utils/check_exam_consistency.py
```

**Validación Post-Extracción**:
```bash
# Después de extraer un nuevo examen
python tools/extraction/madrid_extract_questions.py --input-file nuevo_examen.pdf --test-code 01
python tools/utils/check_exam_consistency.py  # Verificar que mantiene consistencia
```

**Identificación de Problemas**:
Si el script detecta inconsistencias:
1. **Revisar categorización**: Las preguntas pueden estar mal clasificadas por categoría
2. **Re-extraer con script actualizado**: Usar la versión mejorada del extractor
3. **Verificar PDF fuente**: El PDF puede tener estructura diferente

---

## 🚀 Flujo de Procesamiento End-to-End

### Paso 0: Verificación de Consistencia (Recomendado)
**`utils/check_exam_consistency.py`** - Verifica que todos los exámenes YAML existentes sigan la distribución oficial de categorías. Útil para validar la calidad de los datos antes y después de extracciones.

### Paso 1: Extracción de Preguntas
**`extraction/madrid_extract_questions.py`** - Extractor principal que procesa PDFs de exámenes de Madrid y genera archivos YAML con las preguntas estructuradas por categorías.

### Paso 2: Extracción de Respuestas OCR  
**`extraction/madrid_extract_answers_v2.py`** - Extrae respuestas oficiales de PDFs de Madrid usando OCR (reconocimiento óptico de caracteres). Procesa múltiples tipos de examen y genera archivos JSON con las respuestas.

### Paso 3: Aplicación de Respuestas
**`processing/madrid_apply_answers.py`** - Aplica las respuestas extraídas por OCR al archivo YAML de preguntas, generando un backup automático del archivo original.

## 📝 Uso Típico

### Parámetros Estandarizados
Todos los scripts ahora usan una nomenclatura consistente:

```bash
# 0. Verificar consistencia de exámenes existentes (opcional pero recomendado)
python tools/utils/check_exam_consistency.py

# 1. Extraer preguntas del PDF de examen
python tools/extraction/madrid_extract_questions.py --input-file examen.pdf --test-code 01 --verbose

# 2. Extraer respuestas oficiales usando OCR  
python tools/extraction/madrid_extract_answers_v2.py --input-file respuestas.pdf --verbose

# 3. Aplicar respuestas al archivo YAML
python tools/processing/madrid_apply_answers.py --input-file respuestas.json --target-file examen.yaml --verbose

# 4. Verificar consistencia tras la extracción
python tools/utils/check_exam_consistency.py
```

### Parámetros Comunes
- `--input-file`: Archivo principal de entrada (PDF, JSON)
- `--output-dir`: Directorio de salida personalizable 
- `--verbose`: Información detallada del procesamiento
- `--test-code`: Código del test (01, 02, 03, 04, 05, 06)
- `--target-file`: Archivo objetivo a modificar (solo merge)

## 📁 Estructura de Archivos

### Archivos de Entrada
- `data/raw/questions/` - PDFs oficiales de exámenes organizados jerárquicamente
- `data/raw/answers/` - PDFs oficiales de respuestas organizados jerárquicamente

### Archivos de Salida
- `data/exams/questions/` - Archivos YAML finales para la aplicación
- `data/exams/answers/` - Archivos JSON con respuestas oficiales
- `extracted-answers/` - Respuestas extraídas por OCR en formato JSON (temporal)
- `data/backups/` - Copias de seguridad automáticas

## ✅ Proceso Verificado

Este flujo ha sido probado exitosamente con:
- **Examen**: PER Madrid 2025 Test 01 (45 preguntas)
- **Precisión**: 100% verificada contra archivo de referencia
- **Funcionalidad**: Completamente integrado en la aplicación web
- **Consistencia**: 91.8% de exámenes cumplen distribución oficial (45/49 exámenes)

### 📊 Distribución Oficial PER (settings.py)
- **Total**: 45 preguntas en 11 categorías
- **RIPA**: 10 preguntas (categoría principal)
- **Balizamiento**: 5 preguntas
- **Teoría navegación**: 5 preguntas  
- **Nomenclatura, Seguridad, Meteorología, Carta**: 4 preguntas cada una
- **Emergencias**: 3 preguntas
- **Amarre, Legislación, Maniobra**: 2 preguntas cada una

## 🔧 Mantenimiento

### Cuándo Ejecutar el Verificador de Consistencia
- **Antes** de agregar nuevos exámenes
- **Después** de extraer exámenes
- **Periódicamente** para validar integridad del conjunto de datos
- **Antes** de releases o actualizaciones importantes

### Interpretación de Problemas Comunes
- **Seguridad con exceso**: Preguntas de navegación/cartas mal clasificadas
- **RIPA con déficit**: Preguntas de legislación mal clasificadas  
- **Distribución totalmente diferente**: PDF mal procesado, necesita re-extracción

### Configuración
El verificador lee la distribución oficial desde `config/settings.py`:
```python
simulacro_distribution = {
    1: 4,   # Nomenclatura náutica
    2: 2,   # Elementos de amarre y fondeo
    3: 4,   # Seguridad
    4: 2,   # Legislación
    5: 5,   # Balizamiento
    6: 10,  # Reglamento (RIPA)
    7: 2,   # Maniobra y navegación
    8: 3,   # Emergencias en la mar
    9: 4,   # Meteorología
    10: 5,  # Teoría de la navegación
    11: 4   # Carta de navegación
}
```
