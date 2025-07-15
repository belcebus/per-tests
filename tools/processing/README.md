# Processing Tools - Herramientas de Procesamiento

Scripts especializados en procesar y transformar datos extraídos.

## 📄 Scripts Disponibles

### `madrid_apply_answers.py`
**Propósito**: Aplica respuestas oficiales extraídas por OCR a archivos YAML de preguntas.

**Características**:
- Aplicación automática de respuestas a preguntas
- Generación de backups automáticos antes de modificar
- Validación de consistencia entre preguntas y respuestas
- Manejo de respuestas anuladas
- Soporte para múltiples formatos de entrada

**Uso**:
```bash
# Aplicar respuestas usando auto-detección
python tools/processing/madrid_apply_answers.py

# Especificar archivos específicos con información detallada
python tools/processing/madrid_apply_answers.py --input-file respuestas.json --target-file examen.yaml --verbose
```

**Parámetros**:
- `--input-file`: Archivo JSON con respuestas extraídas (opcional, auto-detecta)
- `--target-file`: Archivo YAML del examen a actualizar (opcional, usa default)
- `--output-dir`: Directorio de salida (opcional, usa mismo directorio)
- `--verbose`: Mostrar información detallada del procesamiento

**Entrada**: 
- Archivo YAML con preguntas (en `data/exams/`)
- Archivo JSON con respuestas extraídas (en `extracted_answers/`)

**Salida**: 
- Archivo YAML actualizado con respuestas correctas
- Backup automático del archivo original en `data/backups/`

## 🔄 Flujo de Trabajo

1. **Prerequisitos**: 
   - Archivo YAML con preguntas (generado por `extraction/madrid_extract_questions.py`)
   - Archivo JSON con respuestas (generado por `extraction/madrid_extract_answers.py`)

2. **Procesamiento**:
   ```bash
   # Usar auto-detección (recomendado)
   python tools/processing/madrid_apply_answers.py --verbose
   
   # O especificar archivos manualmente
   python tools/processing/madrid_apply_answers.py --input-file per-test01-respuestas.json --target-file per-test01-examen.yaml
   ```

3. **Verificación**: El script muestra estadísticas de aplicación y posibles inconsistencias

## 🛡️ Seguridad de Datos

- **Backups automáticos**: Se crea una copia de seguridad antes de cualquier modificación
- **Validación**: Verificación de integridad antes y después del procesamiento  
- **Logs detallados**: Registro completo de todas las operaciones realizadas

## 📋 Formato de Entrada

### Archivo JSON de Respuestas
```json
{
  "1": "a",
  "2": "b", 
  "3": "ANULADA",
  "4": "c"
}
```

### Archivo YAML de Preguntas
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

## ⚠️ Consideraciones

- El script modifica archivos de manera permanente (con backup)
- Requiere que las IDs de preguntas coincidan entre JSON y YAML
- Valida que las respuestas estén en el formato correcto (a, b, c, d, ANULADA)
- Reporta cualquier inconsistencia encontrada durante el procesamiento
