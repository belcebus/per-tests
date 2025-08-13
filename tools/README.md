# Tools - Scripts de Procesamiento de PDFs

Este directorio contiene los scripts esenciales para procesar los PDFs oficiales de exámenes y convertirlos a archivos YAML que utiliza la aplicación.


## 📁 Estructura Actualizada de `tools/`

```
tools/
├── extraction/
│   ├── __init__.py
│   ├── images_to_single_text.py
│   ├── pdf_to_images.py
│   ├── txt_to_yaml_per.py
│   ├── madrid/
│   │   ├── madrid_extract_answers_v2.py
│   │   └── madrid_extract_questions.py
│   └── murcia/
│       └── manual_answers_generator.py
├── processing/
│   ├── __init__.py
│   └── madrid_apply_answers.py
├── utils/
│   ├── check_exam_consistency.py
│   └── clean_txt_questions.py
└── README.md
```


### Descripción de los subdirectorios y scripts principales

- **extraction/**  
  Scripts para extraer datos de PDFs, convertir imágenes y generar archivos estructurados.
  - `images_to_single_text.py`: Convierte varias imágenes en un solo texto.
    - **Ejemplo de uso:**
      ```bash
      python tools/extraction/images_to_single_text.py --input-dir carpeta_imagenes --output-file resultado.txt
      ```
  - `pdf_to_images.py`: Extrae imágenes de PDFs.
    - **Ejemplo de uso:**
      ```bash
      python tools/extraction/pdf_to_images.py --input-file examen.pdf --output-dir imagenes_extraidas
      ```
  - `txt_to_yaml_per.py`: Convierte textos en archivos YAML para PER.
    - **Ejemplo de uso:**
      ```bash
      python tools/extraction/txt_to_yaml_per.py --input-file preguntas.txt --output-file preguntas.yaml
      ```
  - **madrid/**: Scripts específicos para exámenes de Madrid.
    - `madrid_extract_questions.py`: Extrae preguntas y estructura de exámenes.
    - `madrid_extract_answers_v2.py`: Extrae respuestas oficiales usando OCR.
  - **murcia/**: Scripts específicos para exámenes de Murcia.
    - `murcia_extract_questions.py`: Extrae preguntas y estructura de exámenes desde PDFs.
    - `manual_answers_generator.py`: Generador manual interactivo de respuestas.

- **processing/**  
  Scripts para procesar y aplicar respuestas a los exámenes.
  - `madrid_apply_answers.py`: Aplica respuestas extraídas a archivos YAML.

- **utils/**  
  Herramientas de utilidad y control de calidad.
  - `check_exam_consistency.py`: Verifica la consistencia de los exámenes.
  - `clean_txt_questions.py`: Limpia y normaliza archivos de preguntas en texto.
    - **Ejemplo de uso:**
      ```bash
      python tools/utils/clean_txt_questions.py --input-file preguntas.txt --output-file preguntas_limpias.txt
      ```

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

## 🚢 MURCIA - Herramientas Específicas para Murcia

## 🚢 MURCIA - Herramientas Específicas para Murcia

### `murcia_extract_questions.py`
**Propósito**: Extractor especializado de preguntas de exámenes PER desde PDFs oficiales de la región de Murcia.

**Características específicas de Murcia**:
- 📋 **Formato único**: Todos los exámenes de Murcia son tipo Test 01 únicamente
- 🔢 **Numeración flexible**: Maneja formatos mixtos "1.-", "1.", "2.-", "2." en el mismo documento
- 📝 **Patrones robustos**: Detecta automáticamente el patrón de numeración predominante
- ✅ **Distribución fija**: Usa la distribución estándar PER de 45 preguntas en 11 categorías
- 🔍 **Detección inteligente**: Reconoce automáticamente año y convocatoria del nombre del archivo
- 🧹 **Limpieza avanzada**: Remueve títulos de sección que se cuelan entre opciones
- 🎯 **Combinación de patrones**: Si un patrón no extrae todas las preguntas, combina múltiples patrones automáticamente

#### Formato Específico de Murcia

**Estructura de Preguntas**:
```
1.- ¿Cuál es la definición de "puntal"?
a) Pieza horizontal del casco...
b) Pieza vertical que une la quilla...
c) Pieza transversal que forma...
d) Pieza longitudinal del forro...
```

**Variaciones de Numeración**:
- `1.- Pregunta...` (formato tradicional)
- `1. Pregunta...` (formato moderno)
- Formatos mixtos en el mismo examen

**Títulos de Sección**:
```
Unidad teórica 1: NOMENCLATURA NÁUTICA
Unidad teórica 6: REGLAMENTO (RIPA)
```

#### Uso desde Línea de Comandos

```bash
# Extraer preguntas de un examen de Murcia (detecta automáticamente año/convocatoria)
python tools/extraction/murcia/murcia_extract_questions.py --input-file PDF_PATH [--output-dir DIRECTORIO] [--verbose]
```

#### Parámetros

**Obligatorios**:
- `--input-file`: Archivo PDF del examen de Murcia

**Opcionales**:
- `--output-dir`: Directorio de salida (default: `data/exams/questions`)
- `--verbose`: Información detallada del procesamiento

#### Detección Automática de Metadatos

El script detecta automáticamente desde el nombre del archivo:
- **Formato esperado**: `murcia-YYYY-convocatoria.pdf`
- **Ejemplos válidos**: `murcia-2024-junio.pdf`, `murcia-2023-noviembre.pdf`

#### Ejemplos de Uso

```bash
# Extraer examen básico
python tools/extraction/murcia/murcia_extract_questions.py --input-file data/raw/questions/murcia/2024/murcia-2024-junio.pdf

# Extraer con información detallada
python tools/extraction/murcia/murcia_extract_questions.py --input-file murcia-2023-marzo.pdf --verbose

# Especificar directorio de salida personalizado
python tools/extraction/murcia/murcia_extract_questions.py --input-file murcia-2022-noviembre.pdf --output-dir mis_examenes

# Ver ayuda completa
python tools/extraction/murcia/murcia_extract_questions.py --help
```

#### Distribución Fija PER de Murcia

```
Pregunta  1-4  : Nomenclatura náutica       (4 preguntas)
Pregunta  5-6  : Elementos de amarre y fondeo (2 preguntas)
Pregunta  7-10 : Seguridad                  (4 preguntas)
Pregunta  11-12: Legislación                (2 preguntas)
Pregunta  13-17: Balizamiento               (5 preguntas)
Pregunta  18-27: Reglamento (RIPA)          (10 preguntas) ← Categoría principal
Pregunta  28-29: Maniobra y navegación      (2 preguntas)
Pregunta  30-32: Emergencias en la mar      (3 preguntas)
Pregunta  33-36: Meteorología               (4 preguntas)
Pregunta  37-41: Teoría de la navegación    (5 preguntas)
Pregunta  42-45: Carta de navegación        (4 preguntas)
```

#### Ejemplo de Sesión de Extracción

```bash
$ python tools/extraction/murcia/murcia_extract_questions.py --input-file murcia-2024-marzo.pdf --verbose

🚢 Extractor de Preguntas PER - Murcia
📅 Año: 2024
📋 Convocatoria: marzo
📄 PDF origen: murcia-2024-marzo.pdf
📁 Directorio salida: data/exams/questions
------------------------------------------------------------
📄 Extrayendo texto de murcia-2024-marzo.pdf
📊 Texto extraído: 125847 caracteres
✅ Inicio del examen encontrado: 'EXAMEN TIPO 1' en posición: 1247
✅ Final del examen: usando final del archivo en posición 124891
📊 Procesando sección del examen: 123644 caracteres
🎯 Mejor patrón individual '(\d+)\.-\s+' encontró 45 preguntas
🔍 Encontradas 45 preguntas numeradas válidas
✅ Extraídas 45 preguntas válidas
🚢 Extrayendo examen de Murcia: 2024 marzo
📄 Archivo: murcia-2024-marzo.pdf
💾 Datos guardados en data/exams/questions/murcia/2024/per-test01-murcia-2024-marzo.yaml

📊 RESUMEN DE EXTRACCIÓN:
   ✅ Preguntas extraídas: 45/45
   📚 Categorías encontradas: 11
   📝 Preguntas con respuestas: 0
   💾 Archivo guardado: data/exams/questions/murcia/2024/per-test01-murcia-2024-marzo.yaml

============================================================
📊 RESUMEN DE PROCESAMIENTO
============================================================
✅ Procesamiento completado sin errores ni advertencias
============================================================
```

#### Manejo Inteligente de Patrones

**Detección Automática del Mejor Patrón**:
- Prioriza patrones que extraen exactamente 45 preguntas
- Calcula puntuación de calidad basada en consecutividad
- Combina múltiples patrones si uno solo no extrae todas las preguntas

**Ejemplo de Combinación de Patrones**:
```bash
🎯 Mejor patrón individual '(\d+)\.-\s+' encontró 42 preguntas
⚠️ Solo 42 preguntas con un patrón, intentando combinación...
✅ Combinación de patrones encontró 45 preguntas
📋 Patrones usados: (\d+)\.-\s+ (42 preguntas), (\d+)\.\s+ (3 preguntas)
```

#### Limpieza Avanzada de Contenido

**Normalización de Caracteres**:
- Convierte comillas problemáticas del PDF (`<texto=` → `"texto"`)
- Normaliza espacios no estándar a espacios regulares

**Filtrado de Elementos No Deseados**:
- Remueve cabeceras/pies: "Tipo 1", "P.E.R. - Tipo 1", "1 / 10"
- Elimina títulos de sección: "Unidad teórica N: NOMBRE"
- Limpia opciones que incluyen títulos de la siguiente sección

#### Validación y Control de Calidad

**Validación por Pregunta**:
- ✅ Longitud mínima del texto (≥10 caracteres)
- ✅ Presencia de las 4 opciones (a, b, c, d)
- ⚠️ Detección de opciones vacías
- ⚠️ Verificación de estructura de pregunta

**Validación Global**:
- 🔍 Identificación de preguntas faltantes
- 📊 Distribución por categorías
- 📈 Estadísticas de extracción

#### Estructura del Archivo YAML Generado

```yaml
exam_info:
  title: "EXAMEN DE PATRÓN DE EMBARCACIONES DE RECREO"
  subtitle: "Código de Test 01"
  total_questions: 45
  expected_questions: 45
  categories: 11
  questions_with_answers: 0
  community: "Murcia"
  year: 2024
  call: "marzo"
  test_code: "test01"

categories:
  1:
    name: "Nomenclatura náutica"
    questions:
      - id: 1
        question: "\"Puntal\" es…"
        options:
          a: "La altura del casco medida en el centro del buque..."
          b: "La anchura máxima del casco..."
          c: "La distancia entre perpendiculares..."
          d: "La longitud de flotación del buque..."
        category: 1
        category_name: "Nomenclatura náutica"
        correct_answer: null
  # ... continúa para las 11 categorías
```

#### Nomenclatura de Archivos

**Archivos de Entrada**:
```
data/raw/questions/murcia/YYYY/murcia-YYYY-convocatoria.pdf
```

**Archivos de Salida**:
```
data/exams/questions/murcia/YYYY/per-test01-murcia-YYYY-convocatoria.yaml
```

#### Casos de Uso Típicos

**Procesamiento de Nuevo Examen**:
```bash
# Descargar PDF oficial → Colocar en data/raw/questions/murcia/2024/
python tools/extraction/murcia/murcia_extract_questions.py --input-file data/raw/questions/murcia/2024/murcia-2024-diciembre.pdf --verbose
```

**Reprocesamiento por Mejoras en el Algoritmo**:
```bash
# Cuando se mejora el extractor, reprocesar exámenes existentes
python tools/extraction/murcia/murcia_extract_questions.py --input-file murcia-2023-junio.pdf
```

**Extracción Masiva**:
```bash
# Procesar múltiples exámenes (ejemplo con bucle bash)
for pdf in data/raw/questions/murcia/*/*.pdf; do
    python tools/extraction/murcia/murcia_extract_questions.py --input-file "$pdf"
done
```

#### Depuración y Resolución de Problemas

**Problemas Comunes y Soluciones**:

1. **Formato de archivo no reconocido**:
   ```
   ❌ Error: Formato de archivo no reconocido: examen-murcia.pdf
   💡 El formato esperado es: murcia-YYYY-convocatoria.pdf
   ```
   **Solución**: Renombrar archivo según el formato esperado

2. **Preguntas faltantes**:
   ```
   ⚠️ WARNING: Preguntas faltantes: [23, 44]
   ```
   **Solución**: Verificar PDF original, pueden estar en formato no estándar

3. **Opciones vacías**:
   ```
   ⚠️ WARNING: Pregunta 15: opciones vacías ['d']
   ```
   **Solución**: Revisar pregunta manualmente, puede requerir limpieza adicional

#### Integración con el Flujo de Trabajo

**Flujo Típico de Murcia**:
```bash
# 1. Extraer preguntas desde PDF
python tools/extraction/murcia/murcia_extract_questions.py --input-file murcia-2024-marzo.pdf

# 2. Generar respuestas manualmente (garantiza 100% precisión)
python tools/extraction/murcia/manual_answers_generator.py

# 3. Verificar consistencia final
python tools/utils/check_exam_consistency.py
```

---

### `manual_answers_generator.py`
**Propósito**: Generador manual interactivo para crear archivos JSON de respuestas correctas de exámenes de Murcia.

**Características**:
- 🎯 **Entrada manual**: Solicita respuestas por línea de comandos con máxima precisión
- 🔢 **Respuestas múltiples**: Soporta preguntas con varias respuestas correctas (ej: `abc`, `bd`)
- ❌ **Preguntas anuladas**: Manejo específico de preguntas anuladas
- ↩️ **Navegación**: Permite retroceder para corregir respuestas anteriores  
- 🔍 **Validación robusta**: Verificación automática de entradas inválidas
- 📊 **Estadísticas**: Resumen y distribución de respuestas antes de confirmar
- 📁 **Estructura automática**: Genera archivos JSON en la ubicación correcta
- 📋 **Modo batch**: Vista general del estado de todos los exámenes

#### Uso desde Línea de Comandos

```bash
# Modo interactivo para crear un examen específico
python tools/extraction/murcia/manual_answers_generator.py

# Ver estado de todos los exámenes disponibles  
python tools/extraction/murcia/manual_answers_generator.py --batch
```

#### Tipos de Respuesta Soportados

**Respuesta Simple**:
```
Q 5/45 - Respuesta(s) correcta(s) (a/b/c/d/abc/bd/anulada): b
```

**Respuestas Múltiples** (tras revisión del examen):
```
Q12/45 - Respuesta(s) correcta(s) (a/b/c/d/abc/bd/anulada): bc
Q27/45 - Respuesta(s) correcta(s) (a/b/c/d/abc/bd/anulada): abd
```

**Preguntas Anuladas**:
```
Q33/45 - Respuesta(s) correcta(s) (a/b/c/d/abc/bd/anulada): anulada
```

#### Comandos de Navegación

- **`atras`**: Volver a la pregunta anterior para corregir
- **`salir`**: Cancelar y abandonar el proceso
- **Validación automática**: Detecta entradas inválidas y solicita corrección

#### Ejemplo de Sesión Interactiva

```bash
$ python tools/extraction/murcia/manual_answers_generator.py

🚢 GENERADOR MANUAL DE RESPUESTAS - MURCIA
============================================================
📅 Año del examen (ej: 2024): 2024
📋 Convocatoria ['marzo', 'abril', 'junio', 'julio', 'octubre', 'noviembre', 'diciembre']: marzo

✅ Configuración: 2024 - marzo
============================================================
📄 Archivo de preguntas encontrado: data/exams/questions/murcia/2024/per-test01-murcia-2024-marzo.yaml

🎯 INTRODUCIENDO RESPUESTAS CORRECTAS
============================================================
Para cada pregunta, introduce la(s) letra(s) de la(s) respuesta(s) correcta(s):
  - Una sola respuesta: a, b, c, d
  - Múltiples respuestas: abc, bd, ac, etc.
  - Pregunta anulada: anulada
También puedes usar 'atras' para volver a la pregunta anterior, 'salir' para cancelar
============================================================

📝 Q1: "Puntal" es…
Q 1/45 - Respuesta(s) correcta(s) (a/b/c/d/abc/bd/anulada): b

📝 Q2: Asiento negativo es…
Q 2/45 - Respuesta(s) correcta(s) (a/b/c/d/abc/bd/anulada): a

# ... continúa para las 45 preguntas ...

📋 RESUMEN DE RESPUESTAS INTRODUCIDAS:
============================================================
Q 1:b | Q 2:a | Q 3:c | Q 4:d | Q 5:c
Q 6:d | Q 7:b | Q 8:d | Q 9:a | Q10:d
Q11:d | Q12:bc | Q13:c | Q14:d | Q15:d
# ... resto del resumen ...

📊 Distribución: {'a': 12, 'b': 11, 'c': 9, 'd': 11, 'múltiple:bc': 1, 'anulada': 1}
📈 Resumen: 42 simples, 2 múltiples, 1 anuladas

✅ ¿Confirmar y generar archivo JSON? (s/n): s

🎉 ÉXITO: Archivo generado correctamente
📁 Ubicación: data/exams/answers/murcia/2024/per-test01-murcia-2024-marzo.json
📊 Total respuestas: 45
📈 Resumen: 42 simples, 2 múltiples, 1 anuladas
```

#### Estructura del Archivo JSON Generado

```json
{
  "exam_type": "PER",
  "test_model": "TEST01", 
  "total_answers": 45,
  "answers": {
    "1": "b",
    "2": "a",
    "3": "c",
    "12": ["b", "c"],
    "27": ["a", "b", "d"],
    "33": "anulada"
  },
  "source_pdf": "murcia-2024-marzo.pdf",
  "generated_at": "2025-08-12T19:07:26.494004",
  "pdf_info": {
    "comunidad": "murcia",
    "año": "2024", 
    "convocatoria": "marzo"
  }
}
```

#### Modo Batch - Estado de Exámenes

```bash
$ python tools/extraction/murcia/manual_answers_generator.py --batch

🚢 MODO BATCH - MÚLTIPLES EXÁMENES
============================================================

📚 EXÁMENES DISPONIBLES (29 total):
============================================================
 1. ✅ 2015-junio
 2. ❌ 2015-noviembre  
 3. ❌ 2015-marzo
 4. ❌ 2016-marzo
 # ... resto de la lista ...

⏳ PENDIENTES DE PROCESAR: 28
  - 2015-noviembre
  - 2015-marzo  
  - 2016-marzo
  # ... resto pendientes ...

✅ YA COMPLETADOS: 1
  - 2015-junio
```

#### Validación de Entrada

El script valida automáticamente:
- **Letras válidas**: Solo acepta `a`, `b`, `c`, `d`
- **Combinaciones**: Permite múltiples letras como `abc`, `bd`, `ac`
- **Comandos especiales**: `anulada`, `atras`, `salir`
- **Entradas vacías**: Detecta y rechaza respuestas en blanco

#### Estructura de Archivos

**Archivos de Entrada** (archivos de preguntas YAML):
```
data/exams/questions/murcia/{año}/per-test01-murcia-{año}-{convocatoria}.yaml
```

**Archivos de Salida** (JSON de respuestas):
```
data/exams/answers/murcia/{año}/per-test01-murcia-{año}-{convocatoria}.json
```

#### Ventajas del Enfoque Manual

- **💯 Precisión Total**: Garantiza 100% exactitud en las respuestas
- **🚀 Eficiencia**: Más rápido que debugging de algoritmos automáticos
- **🔄 Control Total**: Permite corrección inmediata de errores
- **📝 Contexto**: Muestra el texto de cada pregunta durante la entrada
- **🛡️ Seguridad**: Confirmación antes de sobrescribir archivos existentes

#### Casos de Uso

**Procesar Nuevo Examen**:
```bash
# Para un examen específico recién añadido
python tools/extraction/murcia/manual_answers_generator.py
```

**Control de Progreso**:
```bash
# Ver qué exámenes faltan por procesar
python tools/extraction/murcia/manual_answers_generator.py --batch
```

**Corrección de Examen Existente**:
```bash  
# El script pregunta si sobrescribir archivos existentes
python tools/extraction/murcia/manual_answers_generator.py
# Responder 's' cuando pregunte si sobrescribir
```

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
